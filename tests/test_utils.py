"""
Tests for CarriersNetwork in energy_balance_evaluation.utils.
"""

import unittest

import pypsa
import pytest


class TestCarriersNetworkInit(unittest.TestCase):
    """Test CarriersNetwork initialisation with a simple pypsa network."""

    def _make_network(self):
        n = pypsa.Network()
        n.add("Carrier", "gas")
        n.add("Bus", "bus_gas_0", carrier="gas")
        n.add("Bus", "bus_gas_1", carrier="gas")
        n.add("Generator", "gen_gas_0", bus="bus_gas_0", carrier="gas", p_nom=200)
        n.add("Load", "load_gas_1", bus="bus_gas_1", carrier="gas", p_set=100)
        n.add(
            "Link",
            "link_gas",
            bus0="bus_gas_0",
            bus1="bus_gas_1",
            carrier="gas",
            p_nom=150,
        )
        return n

    def test_initialization(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        self.assertEqual(cn.carrier, "gas")

    def test_buses_not_empty(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        self.assertFalse(cn.buses.empty)

    def test_generators_not_empty(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        self.assertFalse(cn.generators.empty)

    def test_loads_not_empty(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        self.assertFalse(cn.loads.empty)

    def test_links_not_empty(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        self.assertFalse(cn.links.empty)

    def test_no_buses_raises(self):
        from energy_balance_evaluation.utils import CarriersNetwork, InputError

        n = pypsa.Network()
        n.add("Carrier", "wind")
        with self.assertRaises(InputError):
            CarriersNetwork("wind", n)

    def test_get_mermaid_string_returns_string(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        mermaid = cn.get_mermaid_string()
        self.assertIsInstance(mermaid, str)

    def test_get_mermaid_string_starts_with_flowchart(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        mermaid = cn.get_mermaid_string()
        self.assertTrue(mermaid.startswith("flowchart LR;"))

    def test_get_mermaid_string_contains_bus(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n)
        mermaid = cn.get_mermaid_string()
        self.assertIn("bus_gas_0", mermaid)


class TestCarriersNetworkBusPattern(unittest.TestCase):
    """Test bus_pattern filtering in CarriersNetwork."""

    def _make_network(self):
        """Network with two buses: bus_gas_AT0 and bus_gas_AT1."""
        n = pypsa.Network()
        n.add("Carrier", "gas")
        n.add("Bus", "bus_gas_AT0", carrier="gas")
        n.add("Bus", "bus_gas_AT1", carrier="gas")
        n.add("Generator", "gen_AT0", bus="bus_gas_AT0", carrier="gas", p_nom=100)
        n.add("Generator", "gen_AT1", bus="bus_gas_AT1", carrier="gas", p_nom=50)
        n.add("Load", "load_AT0", bus="bus_gas_AT0", carrier="gas", p_set=80)
        n.add(
            "Link",
            "link_AT0_AT1",
            bus0="bus_gas_AT0",
            bus1="bus_gas_AT1",
            carrier="gas",
            p_nom=60,
        )
        return n

    def test_bus_pattern_filters_buses(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n, bus_pattern="AT0")
        # Only AT0 bus should be present
        self.assertTrue(all("AT0" in idx for idx in cn.buses.index))

    def test_bus_pattern_filters_generators(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n, bus_pattern="AT0")
        # Only generator attached to AT0 bus
        self.assertEqual(len(cn.generators), 1)
        self.assertEqual(cn.generators.index[0], "gen_AT0")

    def test_bus_pattern_filters_loads(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n, bus_pattern="AT0")
        self.assertEqual(len(cn.loads), 1)
        self.assertEqual(cn.loads.index[0], "load_AT0")

    def test_bus_pattern_keeps_connected_links(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn = CarriersNetwork("gas", n, bus_pattern="AT0")
        # The link between AT0 and AT1 should still be visible
        self.assertFalse(cn.links.empty)

    def test_bus_pattern_no_match_raises(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        with self.assertRaises(Exception):
            CarriersNetwork("gas", n, bus_pattern="NONEXISTENT")

    def test_bus_pattern_mermaid_excludes_other_bus(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network()
        cn_full = CarriersNetwork("gas", n)
        cn_filtered = CarriersNetwork("gas", n, bus_pattern="AT0")
        mermaid_full = cn_full.get_mermaid_string()
        mermaid_filtered = cn_filtered.get_mermaid_string()
        # gen_AT1 should appear in full but not in filtered
        self.assertIn("gen_AT1", mermaid_full)
        self.assertNotIn("gen_AT1", mermaid_filtered)


class TestMultiLink(unittest.TestCase):
    """Test that bus3 / bus4 multilinks are fully handled."""

    def _make_network_with_multilink(self):
        """Network with a 4-port link (bus0..bus3) and a 5-port link (bus0..bus4)."""
        n = pypsa.Network()
        n.add("Carrier", "gas")
        for i in range(5):
            n.add("Bus", f"bus_gas_{i}", carrier="gas")

        # 4-port link: bus0, bus1, bus2, bus3
        n.add(
            "Link",
            "link_4port",
            bus0="bus_gas_0",
            bus1="bus_gas_1",
            bus2="bus_gas_2",
            bus3="bus_gas_3",
            carrier="gas",
            p_nom=100,
        )
        # 5-port link: bus0, bus1, bus2, bus3, bus4
        n.add(
            "Link",
            "link_5port",
            bus0="bus_gas_0",
            bus1="bus_gas_1",
            bus2="bus_gas_2",
            bus3="bus_gas_3",
            bus4="bus_gas_4",
            carrier="gas",
            p_nom=50,
        )
        return n

    def test_get_links_includes_bus3_and_bus4(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network_with_multilink()
        cn = CarriersNetwork("gas", n)
        self.assertFalse(cn.links.empty)
        self.assertIn("link_4port", cn.links.index)
        self.assertIn("link_5port", cn.links.index)

    def test_extra_bus_cols_detects_bus3_bus4(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network_with_multilink()
        cn = CarriersNetwork("gas", n)
        extra = cn._extra_bus_cols(cn.links)
        self.assertIn("bus2", extra)
        self.assertIn("bus3", extra)
        self.assertIn("bus4", extra)

    def test_mermaid_string_contains_bus3_and_bus4(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network_with_multilink()
        cn = CarriersNetwork("gas", n)
        mermaid = cn.get_mermaid_string()
        self.assertIn("bus_gas_3", mermaid)
        self.assertIn("bus_gas_4", mermaid)

    def test_mermaid_string_indirect_edge_label_for_bus3(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = self._make_network_with_multilink()
        cn = CarriersNetwork("gas", n)
        mermaid = cn.get_mermaid_string()
        self.assertIn("indirect bus3", mermaid)
        self.assertIn("indirect bus4", mermaid)


class TestCarrierSearchCascade(unittest.TestCase):
    """
    Test that the carrier is found when it only exists in a non-bus component.
    Covers: link, generator, load, store, storage_unit, and line entry points.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _network_with_link_carrier(self) -> pypsa.Network:
        """Two AC buses + a link whose carrier is 'electrolysis'."""
        n = pypsa.Network()
        n.add("Carrier", "AC")
        n.add("Carrier", "H2")
        n.add("Carrier", "electrolysis")
        n.add("Bus", "bus_AC", carrier="AC")
        n.add("Bus", "bus_H2", carrier="H2")
        n.add(
            "Link",
            "electrolyser",
            bus0="bus_AC",
            bus1="bus_H2",
            carrier="electrolysis",
            p_nom=100,
        )
        return n

    def _network_with_generator_carrier(self) -> pypsa.Network:
        """One AC bus + a generator whose carrier is 'solar' (bus carrier is 'AC')."""
        n = pypsa.Network()
        n.add("Carrier", "AC")
        n.add("Carrier", "solar")
        n.add("Bus", "bus_AC", carrier="AC")
        n.add(
            "Generator",
            "solar_gen",
            bus="bus_AC",
            carrier="solar",
            p_nom=50,
        )
        return n

    def _network_with_load_carrier(self) -> pypsa.Network:
        """One AC bus + a load whose carrier is 'demand'."""
        n = pypsa.Network()
        n.add("Carrier", "AC")
        n.add("Carrier", "demand")
        n.add("Bus", "bus_AC", carrier="AC")
        n.add("Load", "demand_load", bus="bus_AC", carrier="demand", p_set=40)
        return n

    def _network_with_store_carrier(self) -> pypsa.Network:
        """One H2 bus + a store whose carrier is 'h2_store'."""
        n = pypsa.Network()
        n.add("Carrier", "H2")
        n.add("Carrier", "h2_store")
        n.add("Bus", "bus_H2", carrier="H2")
        n.add(
            "Store",
            "h2_tank",
            bus="bus_H2",
            carrier="h2_store",
            e_nom=200,
        )
        return n

    def _network_with_storage_unit_carrier(self) -> pypsa.Network:
        """One AC bus + a storage unit whose carrier is 'battery'."""
        n = pypsa.Network()
        n.add("Carrier", "AC")
        n.add("Carrier", "battery")
        n.add("Bus", "bus_AC", carrier="AC")
        n.add(
            "StorageUnit",
            "battery_su",
            bus="bus_AC",
            carrier="battery",
            p_nom=30,
        )
        return n

    def _network_with_line_carrier(self) -> pypsa.Network:
        """Two AC buses connected by a line with carrier 'AC_line'."""
        n = pypsa.Network()
        n.add("Carrier", "AC")
        n.add("Carrier", "AC_line")
        n.add("Bus", "bus_AC_0", carrier="AC", v_nom=380.0)
        n.add("Bus", "bus_AC_1", carrier="AC", v_nom=380.0)
        n.add(
            "Line",
            "transmission_line",
            bus0="bus_AC_0",
            bus1="bus_AC_1",
            carrier="AC_line",
            x=0.1,
            s_nom=500,
        )
        return n

    # ------------------------------------------------------------------
    # initial_component_type / initial_components attributes
    # ------------------------------------------------------------------

    def test_link_carrier_sets_initial_component_type(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("electrolysis", self._network_with_link_carrier())
        self.assertEqual(cn.initial_component_type, "link")

    def test_link_carrier_initial_components_correct(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("electrolysis", self._network_with_link_carrier())
        self.assertIn("electrolyser", cn.initial_components.index)

    def test_generator_carrier_sets_initial_component_type(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("solar", self._network_with_generator_carrier())
        self.assertEqual(cn.initial_component_type, "generator")

    def test_load_carrier_sets_initial_component_type(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("demand", self._network_with_load_carrier())
        self.assertEqual(cn.initial_component_type, "load")

    def test_store_carrier_sets_initial_component_type(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("h2_store", self._network_with_store_carrier())
        self.assertEqual(cn.initial_component_type, "store")

    def test_storage_unit_carrier_sets_initial_component_type(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("battery", self._network_with_storage_unit_carrier())
        self.assertEqual(cn.initial_component_type, "storage_unit")

    def test_line_carrier_sets_initial_component_type(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("AC_line", self._network_with_line_carrier())
        self.assertEqual(cn.initial_component_type, "line")

    # ------------------------------------------------------------------
    # Buses are populated from connected components
    # ------------------------------------------------------------------

    def test_link_carrier_buses_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("electrolysis", self._network_with_link_carrier())
        self.assertFalse(cn.buses.empty)
        self.assertIn("bus_AC", cn.buses.index)
        self.assertIn("bus_H2", cn.buses.index)

    def test_generator_carrier_buses_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("solar", self._network_with_generator_carrier())
        self.assertFalse(cn.buses.empty)
        self.assertIn("bus_AC", cn.buses.index)

    def test_load_carrier_buses_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("demand", self._network_with_load_carrier())
        self.assertIn("bus_AC", cn.buses.index)

    def test_store_carrier_buses_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("h2_store", self._network_with_store_carrier())
        self.assertIn("bus_H2", cn.buses.index)

    def test_storage_unit_carrier_buses_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("battery", self._network_with_storage_unit_carrier())
        self.assertIn("bus_AC", cn.buses.index)

    def test_line_carrier_buses_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("AC_line", self._network_with_line_carrier())
        self.assertIn("bus_AC_0", cn.buses.index)
        self.assertIn("bus_AC_1", cn.buses.index)

    # ------------------------------------------------------------------
    # All connected components are populated after bus discovery
    # ------------------------------------------------------------------

    def test_link_carrier_links_populated(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("electrolysis", self._network_with_link_carrier())
        self.assertFalse(cn.links.empty)
        self.assertIn("electrolyser", cn.links.index)

    def test_generator_carrier_generators_populated(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("solar", self._network_with_generator_carrier())
        # generator is found via bus; bus-connected generators are returned
        self.assertIn("solar_gen", cn.generators.index)

    def test_load_carrier_loads_populated(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("demand", self._network_with_load_carrier())
        self.assertIn("demand_load", cn.loads.index)

    def test_store_carrier_stores_populated(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("h2_store", self._network_with_store_carrier())
        self.assertIn("h2_tank", cn.stores.index)

    def test_storage_unit_carrier_storage_units_populated(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("battery", self._network_with_storage_unit_carrier())
        self.assertIn("battery_su", cn.storage_units.index)

    # ------------------------------------------------------------------
    # Mermaid output is valid and starts with flowchart
    # ------------------------------------------------------------------

    def test_link_carrier_mermaid_valid(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("electrolysis", self._network_with_link_carrier())
        mermaid = cn.get_mermaid_string()
        self.assertTrue(mermaid.startswith("flowchart LR;"))
        self.assertIn("bus_AC", mermaid)

    def test_generator_carrier_mermaid_valid(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("solar", self._network_with_generator_carrier())
        mermaid = cn.get_mermaid_string()
        self.assertTrue(mermaid.startswith("flowchart LR;"))
        self.assertIn("bus_AC", mermaid)

    def test_load_carrier_mermaid_valid(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("demand", self._network_with_load_carrier())
        mermaid = cn.get_mermaid_string()
        self.assertTrue(mermaid.startswith("flowchart LR;"))

    # ------------------------------------------------------------------
    # Mermaid output highlights initial components
    # ------------------------------------------------------------------

    def test_bus_carrier_mermaid_has_style_for_bus(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = pypsa.Network()
        n.add("Carrier", "gas")
        n.add("Bus", "bus_gas_0", carrier="gas")
        n.add("Generator", "gen_gas_0", bus="bus_gas_0", carrier="gas", p_nom=10)
        cn = CarriersNetwork("gas", n)
        mermaid = cn.get_mermaid_string()
        # style statement for the bus node must be present
        self.assertIn("style BUS_bus_gas_0", mermaid)

    def test_generator_carrier_mermaid_has_style_for_generator(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("solar", self._network_with_generator_carrier())
        mermaid = cn.get_mermaid_string()
        # style statement for the generator node must be present
        self.assertIn("style solar_gen", mermaid)

    def test_link_carrier_mermaid_uses_thick_arrow(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("electrolysis", self._network_with_link_carrier())
        mermaid = cn.get_mermaid_string()
        # thick arrow (==>) is used for initial link edges
        self.assertIn("==>", mermaid)

    def test_load_carrier_mermaid_has_style_for_load(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("demand", self._network_with_load_carrier())
        mermaid = cn.get_mermaid_string()
        self.assertIn("style demand_load", mermaid)

    def test_store_carrier_mermaid_has_style_for_store(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("h2_store", self._network_with_store_carrier())
        mermaid = cn.get_mermaid_string()
        self.assertIn("style h2_tank", mermaid)

    def test_storage_unit_carrier_mermaid_has_style_for_storage_unit(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("battery", self._network_with_storage_unit_carrier())
        mermaid = cn.get_mermaid_string()
        self.assertIn("style battery_su", mermaid)

    # ------------------------------------------------------------------
    # InputError raised when carrier not found anywhere
    # ------------------------------------------------------------------

    def test_input_error_when_carrier_not_found(self):
        from energy_balance_evaluation.utils import CarriersNetwork, InputError

        n = pypsa.Network()
        n.add("Carrier", "coal")
        n.add("Bus", "bus_coal", carrier="coal")
        with self.assertRaises(InputError):
            CarriersNetwork("nonexistent_carrier", n)

    # ------------------------------------------------------------------
    # bus_pattern still works for non-bus entry
    # ------------------------------------------------------------------

    def test_bus_pattern_works_with_link_carrier(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        n = pypsa.Network()
        n.add("Carrier", "AC")
        n.add("Carrier", "H2")
        n.add("Carrier", "electrolysis")
        n.add("Bus", "AT0 AC", carrier="AC")
        n.add("Bus", "AT1 AC", carrier="AC")
        n.add("Bus", "AT0 H2", carrier="H2")
        n.add("Bus", "AT1 H2", carrier="H2")
        n.add(
            "Link",
            "AT0 electrolyser",
            bus0="AT0 AC",
            bus1="AT0 H2",
            carrier="electrolysis",
            p_nom=100,
        )
        n.add(
            "Link",
            "AT1 electrolyser",
            bus0="AT1 AC",
            bus1="AT1 H2",
            carrier="electrolysis",
            p_nom=80,
        )
        cn = CarriersNetwork("electrolysis", n, bus_pattern="AT0")
        # Only AT0 buses should remain after filtering
        self.assertTrue(all("AT0" in idx for idx in cn.buses.index))
        # AT1 link should be excluded
        self.assertNotIn("AT1 electrolyser", cn.links.index)


class TestStoresInMermaid(unittest.TestCase):
    """Verify that stores appear in the Mermaid output."""

    def _make_network(self) -> pypsa.Network:
        n = pypsa.Network()
        n.add("Carrier", "H2")
        n.add("Bus", "bus_H2", carrier="H2")
        n.add("Store", "h2_cavern", bus="bus_H2", carrier="H2", e_nom=1000)
        return n

    def test_store_appears_in_mermaid(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("H2", self._make_network())
        mermaid = cn.get_mermaid_string()
        self.assertIn("h2_cavern", mermaid)

    def test_store_node_format(self):
        from energy_balance_evaluation.utils import CarriersNetwork

        cn = CarriersNetwork("H2", self._make_network())
        mermaid = cn.get_mermaid_string()
        # store nodes use the (STORE ...) shape
        self.assertIn("STORE h2_cavern", mermaid)


if __name__ == "__main__":
    unittest.main()
