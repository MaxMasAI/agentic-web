"""
test_fancyzones_manager.py - Test suite for PowerToys FancyZones layout engine.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from system.fancyzones_manager import (
    FancyZone,
    calculate_3_columns_layout,
    calculate_dynamic_columns_layout,
    calculate_priority_grid_layout,
    calculate_grid_4_layout,
    calculate_focus_3_layout,
    get_fancyzones_layout,
    calculate_zone_bounds
)


class TestFancyZonesManager(unittest.TestCase):

    def setUp(self):
        self.screen_w = 1920
        self.screen_h = 1080
        self.spacing = 16
        self.taskbar_margin = 40

    def test_3_columns_layout_bounds(self):
        """Verify 3-column FancyZone layout fits screen and preserves 16px gaps."""
        zones = calculate_3_columns_layout(
            self.screen_w, self.screen_h,
            spacing=self.spacing,
            show_spacing=True,
            taskbar_margin=self.taskbar_margin
        )
        self.assertEqual(len(zones), 3)

        # Check zone 0 (Left)
        z0 = zones[0]
        self.assertEqual(z0.x, self.spacing)
        self.assertEqual(z0.y, self.spacing)

        # Check zone 1 (Middle)
        z1 = zones[1]
        self.assertEqual(z1.x, z0.x + z0.width + self.spacing)
        self.assertEqual(z1.y, self.spacing)

        # Check zone 2 (Right)
        z2 = zones[2]
        self.assertEqual(z2.x, z1.x + z1.width + self.spacing)
        self.assertEqual(z2.y, self.spacing)

        # Ensure no overflow
        self.assertLessEqual(z2.x + z2.width, self.screen_w)
        self.assertLessEqual(z0.y + z0.height, self.screen_h)

    def test_calculate_zone_bounds_helper(self):
        """Verify calculate_zone_bounds returns valid tuples."""
        b0 = calculate_zone_bounds(0, total_agents=3, screen_w=1920, screen_h=1080, spacing=16)
        b1 = calculate_zone_bounds(1, total_agents=3, screen_w=1920, screen_h=1080, spacing=16)
        b2 = calculate_zone_bounds(2, total_agents=3, screen_w=1920, screen_h=1080, spacing=16)

        self.assertEqual(len(b0), 4)
        self.assertEqual(len(b1), 4)
        self.assertEqual(len(b2), 4)

        # Widths and heights are positive and reasonable
        self.assertGreater(b0[2], 300)
        self.assertGreater(b0[3], 500)

    def test_priority_grid(self):
        """Verify Priority Grid contains 3 zones (Main leader left, 2 stacked right)."""
        zones = calculate_priority_grid_layout(self.screen_w, self.screen_h, spacing=16)
        self.assertEqual(len(zones), 3)
        self.assertGreater(zones[0].height, zones[1].height)

    def test_dynamic_columns(self):
        """Verify dynamic column calculations for 1, 2, 4 agents."""
        for count in [1, 2, 4, 5]:
            zones = calculate_dynamic_columns_layout(count, self.screen_w, self.screen_h, spacing=16)
            self.assertEqual(len(zones), count)
            for z in zones:
                self.assertGreater(z.width, 50)
                self.assertLessEqual(z.x + z.width, self.screen_w)


if __name__ == "__main__":
    unittest.main()
