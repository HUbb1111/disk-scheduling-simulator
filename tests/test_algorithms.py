"""Regression and edge-case tests for the disk scheduling algorithms."""

import unittest

from algorithms import c_scan, fcfs, run_all, scan, sstf
from main import DIRECTION_OPTIONS, parse_simulation_inputs


class DiskSchedulingAlgorithmTests(unittest.TestCase):
    REQUESTS = (98, 183, 37, 122, 14, 124, 65, 67)
    HEAD = 53

    def test_textbook_sample_totals_and_service_orders(self) -> None:
        results = run_all(self.REQUESTS, self.HEAD, 0, 199, "up")
        by_name = {result.algorithm: result for result in results}

        self.assertEqual(
            {name: result.total_movement for name, result in by_name.items()},
            {"FCFS": 640, "SSTF": 236, "SCAN": 331, "C-SCAN": 382},
        )
        self.assertEqual(by_name["FCFS"].service_order, self.REQUESTS)
        self.assertEqual(by_name["SSTF"].service_order, (65, 67, 37, 14, 98, 122, 124, 183))
        self.assertEqual(by_name["SCAN"].service_order, (65, 67, 98, 122, 124, 183, 37, 14))
        self.assertEqual(by_name["C-SCAN"].service_order, (65, 67, 98, 122, 124, 183, 14, 37))
        self.assertEqual(by_name["C-SCAN"].movement_sequence, (53, 65, 67, 98, 122, 124, 183, 199, 0, 14, 37))
        self.assertEqual(by_name["C-SCAN"].circular_jumps, (7,))

    def test_distances_and_average_include_physical_boundary_and_wrap_travel(self) -> None:
        results = run_all(self.REQUESTS, self.HEAD, 0, 199, "up")
        for result in results:
            self.assertEqual(
                result.movement_distances,
                tuple(
                    abs(end - start)
                    for start, end in zip(result.movement_sequence, result.movement_sequence[1:])
                ),
            )
            self.assertEqual(sum(result.movement_distances), result.total_movement)
            self.assertAlmostEqual(result.average_seek_distance, result.total_movement / len(self.REQUESTS))

    def test_requests_at_head_and_duplicate_requests_add_no_phantom_movement(self) -> None:
        result = fcfs((50, 50, 60), head=50, min_cylinder=0, max_cylinder=199)
        self.assertEqual(result.service_order, (50, 50, 60))
        self.assertEqual(result.movement_sequence, (50, 60))
        self.assertEqual(result.service_steps, (0, 0, 1))
        self.assertEqual(result.movement_distances, (10,))
        self.assertEqual(result.total_movement, 10)

    def test_scan_reaches_boundary_before_reversing(self) -> None:
        result = scan((10, 20), head=50, min_cylinder=0, max_cylinder=199, direction="up")
        self.assertEqual(result.movement_sequence, (50, 199, 20, 10))
        self.assertEqual(result.total_movement, 338)

    def test_c_scan_wrap_is_physical_travel_not_a_request(self) -> None:
        result = c_scan((10, 20), head=50, min_cylinder=0, max_cylinder=199, direction="up")
        self.assertEqual(result.movement_sequence, (50, 199, 0, 10, 20))
        self.assertEqual(result.service_order, (10, 20))
        self.assertEqual(result.circular_jumps, (1,))
        self.assertEqual(result.total_movement, 368)

    def test_scan_and_c_scan_follow_the_lower_cylinder_direction(self) -> None:
        requests = (10, 20, 60, 90)
        scan_result = scan(requests, 50, 0, 199, "down")
        circular_result = c_scan(requests, 50, 0, 199, "down")

        self.assertEqual(scan_result.movement_sequence, (50, 20, 10, 0, 60, 90))
        self.assertEqual(scan_result.service_order, (20, 10, 60, 90))
        self.assertEqual(scan_result.total_movement, 140)
        self.assertEqual(circular_result.movement_sequence, (50, 20, 10, 0, 199, 90, 60))
        self.assertEqual(circular_result.service_order, (20, 10, 90, 60))
        self.assertEqual(circular_result.circular_jumps, (3,))
        self.assertEqual(circular_result.total_movement, 388)

    def test_sstf_breaks_equal_distance_ties_by_input_order(self) -> None:
        result = sstf((60, 40), head=50, min_cylinder=0, max_cylinder=199)
        self.assertEqual(result.service_order, (60, 40))

    def test_invalid_disk_inputs_are_rejected(self) -> None:
        invalid_calls = (
            lambda: fcfs((), 50),
            lambda: fcfs((200,), 50, 0, 199),
            lambda: fcfs((10,), -1, 0, 199),
            lambda: fcfs((10,), 50, 0, 199, "sideways"),
            lambda: fcfs((1.5,), 50),
        )
        for call in invalid_calls:
            with self.subTest(call=call):
                with self.assertRaises(ValueError):
                    call()

    def test_form_validation_accepts_head_request_and_rejects_bad_inputs(self) -> None:
        direction_label = next(iter(DIRECTION_OPTIONS))
        parsed = parse_simulation_inputs("50", "0", "199", "50, 60", direction_label)
        self.assertEqual(parsed, ([50, 60], 50, 0, 199, "up"))

        invalid_inputs = (
            ("53", "0", "199", "", direction_label, "at least one"),
            ("53", "0", "199", "abc", direction_label, "whole cylinder"),
            ("53", "0", "199", "-1", direction_label, "cannot be negative"),
            ("53", "0", "199", "200", direction_label, "outside the disk boundaries"),
            ("200", "0", "199", "10", direction_label, "Initial head"),
            ("53", "0", "199", "10, 10", direction_label, "Duplicate"),
            ("53", "-1", "199", "10", direction_label, "cannot be negative"),
            ("53", "0", "199", "10", "invalid direction", "valid initial direction"),
        )
        for head, minimum, maximum, requests, direction, message in invalid_inputs:
            with self.subTest(head=head, minimum=minimum, requests=requests, direction=direction):
                with self.assertRaisesRegex(ValueError, message):
                    parse_simulation_inputs(head, minimum, maximum, requests, direction)


if __name__ == "__main__":
    unittest.main()
