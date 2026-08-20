"""unittest suite for RLRRequestProcessor.

Test cases and organization follow tests.md at the repo root. Run with:
    python -m unittest
from the repository root.
"""
import unittest

from rlr.models import RLRRequest, RLRResult
from rlr.processor import RLRRequestProcessor


def make_request(car_id="car-1", stop_line=((5.0, 100.0), (15.0, 100.0)), trajectory=()):
    return RLRRequest(car_id=car_id, stop_line=stop_line, trajectory=list(trajectory))


class RLRTestCase(unittest.TestCase):
    """Shared helpers for all test classes below (tests.md: unittest structure)."""

    def setUp(self):
        self.processor = RLRRequestProcessor()

    def assertTimestampAlmostEqual(self, actual, expected, places=6):
        self.assertIsNotNone(actual, "expected a numeric crossing_timestamp, got None")
        self.assertAlmostEqual(actual, expected, places=places)


class TestNoCrossing(RLRTestCase):
    def test_empty_trajectory_returns_none(self):
        result = self.processor.process_request(make_request(trajectory=[]))
        self.assertIsNone(result.crossing_timestamp)

    def test_single_point_trajectory_returns_none(self):
        request = make_request(trajectory=[(10.0, 0.0, 0.0)])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_single_point_trajectory_on_line_returns_none(self):
        # The one point lies exactly on the stop-line; still no crossing (spec: a single
        # point can never establish a transition, regardless of on-line status).
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(10.0, 8.0, 100.0)],
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)


class TestRLRResultShape(RLRTestCase):
    def test_result_car_id_matches_request(self):
        request = make_request(car_id="car-42", trajectory=[])
        result = self.processor.process_request(request)
        self.assertEqual(result.car_id, "car-42")

    def test_no_crossing_returns_crossing_timestamp_none(self):
        result = self.processor.process_request(make_request(trajectory=[]))
        self.assertIsInstance(result, RLRResult)
        self.assertIsNone(result.crossing_timestamp)


class TestWorkedExamples(RLRTestCase):
    """tests.md section 1 - all eight worked examples from the assignment."""

    def test_example_1_interpolated_crossing_returns_12_5(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(10, 7, 90), (11, 8, 95), (12, 7, 98), (13, 7, 102)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 12.5)

    def test_example_2_never_reaches_line_returns_none(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 97.0)),
            trajectory=[(10, 7, 90), (11, 8, 95), (12, 7, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_example_3_tilted_line_interpolated_crossing_returns_12_35(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 97.0)),
            trajectory=[(10, 7, 90), (11, 8, 95), (12, 7, 98), (13, 7, 102)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 12.35)

    def test_example_4_touch_and_stop_returns_none(self):
        request = make_request(
            stop_line=((9.0, 97.0), (19.0, 94.0)),
            trajectory=[(10, 7, 90), (11, 8, 95), (12, 9, 97)],
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_example_5_sampled_on_line_crossing_returns_11_0(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(10, 8, 102), (11, 8, 100), (12, 8, 98)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 11.0)

    def test_example_6_crosses_infinite_line_outside_segment_returns_none(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(10, 20, 102), (11, 20, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_example_7_graze_and_retreat_returns_none(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(10, 8, 101.5), (11, 8, 100), (12, 8, 101.5)],
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_example_8_two_on_line_samples_raises_value_error(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(10, 8, 100), (11, 9, 100.5)],
        )
        with self.assertRaises(ValueError):
            self.processor.process_request(request)


class TestValidCrossings(RLRTestCase):
    """tests.md section 2 - basic valid crossings beyond the worked examples."""

    def test_vertical_stopline_interpolated_crossing(self):
        request = make_request(
            stop_line=((10.0, 5.0), (10.0, 15.0)),
            trajectory=[(0, 5, 8), (1, 15, 8)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 0.5)

    def test_vertical_stopline_sampled_on_line_crossing(self):
        request = make_request(
            stop_line=((10.0, 5.0), (10.0, 15.0)),
            trajectory=[(0, 5, 8), (1, 10, 8), (2, 15, 8)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_crossing_from_positive_to_negative_side(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(0, 8, 102), (1, 8, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)

    def test_crossing_from_negative_to_positive_side(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(0, 8, 98), (1, 8, 102)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)

    def test_crossing_with_integer_valued_coordinates_and_timestamps(self):
        request = make_request(
            stop_line=((5, 100), (15, 100)),
            trajectory=[(10, 8, 102), (11, 8, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)

    def test_crossing_with_floating_point_coordinates(self):
        request = make_request(
            stop_line=((5.25, 100.5), (15.75, 100.5)),
            trajectory=[(10.1, 8.3, 102.7), (11.2, 8.3, 98.1)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)


class TestFiniteSegmentVsInfiniteLine(RLRTestCase):
    """tests.md section 5 - endpoint / capsule-tolerance behavior (Finding 1)."""

    def test_interpolated_crossing_exactly_at_endpoint_a(self):
        # Straddling samples chosen so the true crossing is exactly at A=(5,100).
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(0, 5, 102), (1, 5, 98)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 0.5)

    def test_interpolated_crossing_slightly_beyond_second_endpoint(self):
        # context.md's Finding 1 running example: (15.5, 100) is 0.5px past B=(15,100).
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(0, 15.5, 102), (1, 15.5, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)

    def test_interpolated_crossing_well_outside_segment_returns_none(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.0)),
            trajectory=[(0, 20, 102), (1, 20, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)


class TestToleranceBoundaries(RLRTestCase):
    """tests.md section 4 - the one-pixel tolerance boundary (Findings 1, 2, 7)."""

    def test_sampled_point_distance_zero_is_on_line(self):
        request = make_request(trajectory=[(0, 8, 102), (1, 8, 100), (2, 8, 98)])
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_sampled_point_distance_less_than_one_is_on_line(self):
        request = make_request(trajectory=[(0, 8, 102), (1, 8, 100.5), (2, 8, 98)])
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_sampled_point_distance_exactly_one_is_on_line(self):
        request = make_request(trajectory=[(0, 8, 102.5), (1, 8, 101.0), (2, 8, 98)])
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_sampled_point_distance_just_over_one_is_strict_side(self):
        # 101.01 is 1.01px away - just past the tolerance - so it's classified strictly
        # on the same side as the first sample (101.01 > 100), not on-line, and the
        # crossing is found by interpolation against the later opposite-side sample
        # instead of landing exactly on this sample's timestamp.
        request = make_request(trajectory=[(0, 8, 102.5), (1, 8, 101.01), (2, 8, 98)])
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)
        self.assertNotAlmostEqual(result.crossing_timestamp, 1.0, places=6)

    def test_sampled_point_near_endpoint_within_capsule_is_on_line(self):
        # (15.9, 100) is beyond the segment's x-range but only 0.9px from endpoint B.
        request = make_request(trajectory=[(0, 8, 102), (1, 15.9, 100), (2, 8, 98)])
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_sampled_point_near_endpoint_just_outside_capsule_is_strict_side(self):
        # (16.1, 100.1) is ~1.10px from endpoint B - just past the capsule.
        request = make_request(trajectory=[(0, 8, 102), (1, 16.1, 100.1), (2, 8, 98)])
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)
        self.assertNotAlmostEqual(result.crossing_timestamp, 1.0, places=6)

    def test_interpolation_targets_exact_line_not_tolerance_band_edge(self):
        # Coordinates chosen well clear of the 1px band on both sides, and non-negative
        # (image coordinates); expected value hand-computed from the exact-line formula.
        request = make_request(
            stop_line=((0.0, 50.0), (10.0, 50.0)),
            trajectory=[(0, 5, 20), (1, 5, 90)],
        )
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 300 / 700)


class TestSampledOnLineBehavior(RLRTestCase):
    """tests.md section 6 - combinations around a single on-line sampled point."""

    def test_side_a_on_line_side_b_sample_transition(self):
        request = make_request(trajectory=[(0, 8, 103), (1, 8, 100), (2, 8, 97)])
        result = self.processor.process_request(request)
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_side_a_on_line_side_a_no_crossing(self):
        request = make_request(trajectory=[(0, 8, 101.2), (1, 8, 100), (2, 8, 101.3)])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_on_line_first_point_then_one_side_returns_none(self):
        request = make_request(trajectory=[(0, 8, 100), (1, 8, 103), (2, 8, 104)])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_on_line_last_point_after_one_side_returns_none(self):
        request = make_request(trajectory=[(0, 8, 103), (1, 8, 104), (2, 8, 100)])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_one_on_line_point_off_transition_no_crossing_returns_none(self):
        request = make_request(
            trajectory=[(0, 8, 103), (1, 8, 104), (2, 8, 100), (3, 8, 105)]
        )
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_more_than_two_on_line_samples_raises_value_error(self):
        request = make_request(
            trajectory=[(0, 8, 100), (1, 9, 100.5), (2, 10, 100.8)]
        )
        with self.assertRaises(ValueError):
            self.processor.process_request(request)

    def test_three_on_line_samples_between_strict_boundaries_raises_value_error(self):
        # critic.md Objection 1's exact scenario: [strict, on-line x3, strict].
        request = make_request(
            trajectory=[(0, 8, 98), (1, 8, 100), (2, 9, 100.3), (3, 10, 99.8), (4, 8, 102)]
        )
        with self.assertRaises(ValueError):
            self.processor.process_request(request)


class TestStopLineValidation(RLRTestCase):
    """tests.md section 7."""

    def test_stopline_malformed_cases_raise_value_error(self):
        cases = {
            "identical_endpoints": ((5.0, 100.0), (5.0, 100.0)),
            "negative_x": ((-1.0, 100.0), (15.0, 100.0)),
            "negative_y": ((5.0, -1.0), (15.0, 100.0)),
            "nonnumeric_coordinate": (("five", 100.0), (15.0, 100.0)),
            "nan_coordinate": ((float("nan"), 100.0), (15.0, 100.0)),
            "positive_infinity_coordinate": ((float("inf"), 100.0), (15.0, 100.0)),
            "negative_infinity_coordinate": ((float("-inf"), 100.0), (15.0, 100.0)),
            "malformed_point_arity": ((5.0, 100.0, 1.0), (15.0, 100.0)),
            "none_point": (None, (5.0, 5.0)),
        }
        for description, stop_line in cases.items():
            with self.subTest(description=description):
                request = make_request(stop_line=stop_line, trajectory=[])
                with self.assertRaises(ValueError):
                    self.processor.process_request(request)

    def test_vertical_stopline_is_accepted(self):
        request = make_request(stop_line=((10.0, 5.0), (10.0, 15.0)), trajectory=[])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_zero_valued_coordinates_are_valid(self):
        request = make_request(stop_line=((0.0, 0.0), (10.0, 0.0)), trajectory=[])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)

    def test_very_short_nondegenerate_stopline_is_valid(self):
        request = make_request(stop_line=((5.0, 100.0), (5.000001, 100.0)), trajectory=[])
        result = self.processor.process_request(request)
        self.assertIsNone(result.crossing_timestamp)


class TestTrajectoryValidation(RLRTestCase):
    """tests.md section 8."""

    def test_trajectory_malformed_point_cases_raise_value_error(self):
        cases = {
            "negative_x": (8, -1.0, 98.0),
            "negative_y": (8, 8.0, -1.0),
            "nonnumeric_coordinate": (8, "eight", 98.0),
            "nan_coordinate": (8, float("nan"), 98.0),
            "infinite_coordinate": (8, float("inf"), 98.0),
            "malformed_arity": (8, 8.0),
            "none_coordinate": (8, None, 98.0),
            "nonnumeric_timestamp": ("ten", 8.0, 98.0),
            "nan_timestamp": (float("nan"), 8.0, 98.0),
            "positive_infinity_timestamp": (float("inf"), 8.0, 98.0),
            "negative_infinity_timestamp": (float("-inf"), 8.0, 98.0),
        }
        for description, bad_point in cases.items():
            with self.subTest(description=description):
                request = make_request(trajectory=[(0, 8, 102), bad_point, (2, 8, 98)])
                with self.assertRaises(ValueError):
                    self.processor.process_request(request)

    def test_trajectory_none_sample_raises_value_error(self):
        request = make_request(trajectory=[(0, 8, 102), None, (2, 8, 98)])
        with self.assertRaises(ValueError):
            self.processor.process_request(request)


class TestCarIdValidation(RLRTestCase):
    """tests.md section 9."""

    def test_car_id_normal_string_is_valid(self):
        request = make_request(car_id="car-42", trajectory=[])
        result = self.processor.process_request(request)
        self.assertEqual(result.car_id, "car-42")

    def test_car_id_malformed_cases_raise_value_error(self):
        cases = {"empty": "", "whitespace_only": "   ", "non_string": 123}
        for description, car_id in cases.items():
            with self.subTest(description=description):
                request = make_request(car_id=car_id, trajectory=[])
                with self.assertRaises(ValueError):
                    self.processor.process_request(request)


class TestTotality(RLRTestCase):
    """tests.md section 10 - ValueError or a valid result, nothing else."""

    def test_extreme_magnitude_coordinates_do_not_leak_unhandled_exception(self):
        # critic.md Objection 3's exact scenario: finite, non-negative, legal-looking
        # coordinates large enough to overflow during geometric classification.
        request = make_request(
            stop_line=((0.0, 0.0), (1e200, 1e200)),
            trajectory=[(0, 1e200, 0.0), (1, 0.0, 1e200)],
        )
        try:
            self.processor.process_request(request)
        except ValueError:
            pass  # acceptable: ValueError is a valid total-processor outcome
        except Exception as exc:  # pragma: no cover
            self.fail(f"expected ValueError or a valid result, got {type(exc).__name__}")

    def test_none_stopline_point_does_not_leak_attribute_error(self):
        request = make_request(stop_line=(None, (5.0, 5.0)), trajectory=[])
        with self.assertRaises(ValueError):
            self.processor.process_request(request)

    def test_malformed_arity_does_not_leak_index_error(self):
        request = make_request(trajectory=[(0, 8, 102), (1, 8.0), (2, 8, 98)])
        with self.assertRaises(ValueError):
            self.processor.process_request(request)


class TestLargeTrajectories(RLRTestCase):
    """tests.md section 12."""

    @staticmethod
    def _large_trajectory(tail_len=99_997):
        stop_line = ((5.0, 100.0), (15.0, 100.0))
        trajectory = [(0, 8, 102), (1, 8, 100), (2, 8, 98)]
        trajectory.extend((3 + i, 8, 98) for i in range(tail_len))
        return stop_line, trajectory

    def test_large_valid_trajectory_100000_points_processes_successfully(self):
        stop_line, trajectory = self._large_trajectory()
        result = self.processor.process_request(make_request(stop_line=stop_line, trajectory=trajectory))
        self.assertTimestampAlmostEqual(result.crossing_timestamp, 1.0)

    def test_large_trajectory_malformed_sample_near_end_raises_value_error(self):
        stop_line, trajectory = self._large_trajectory()
        last_t = trajectory[-1][0]
        trajectory[-1] = (last_t, -1.0, 98.0)
        with self.assertRaises(ValueError):
            self.processor.process_request(make_request(stop_line=stop_line, trajectory=trajectory))

    def test_large_trajectory_second_on_line_sample_near_end_raises_value_error(self):
        stop_line, trajectory = self._large_trajectory()
        trajectory.append((trajectory[-1][0] + 1, 8, 100))
        with self.assertRaises(ValueError):
            self.processor.process_request(make_request(stop_line=stop_line, trajectory=trajectory))


class TestFloatingPointRobustness(RLRTestCase):
    """tests.md section 11 (subset - see IMPLEMENTATION_NOTES.md for Objection 2's
    non-unittest verification)."""

    def test_nearly_vertical_stopline_interpolated_crossing(self):
        request = make_request(
            stop_line=((10.0, 5.0), (10.000001, 15.0)),
            trajectory=[(0, 5, 8), (1, 15, 8)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)

    def test_nearly_horizontal_stopline_interpolated_crossing(self):
        request = make_request(
            stop_line=((5.0, 100.0), (15.0, 100.000001)),
            trajectory=[(0, 8, 102), (1, 8, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)

    def test_very_short_valid_segment_interpolated_crossing(self):
        request = make_request(
            stop_line=((10.0, 100.0), (10.01, 100.0)),
            trajectory=[(0, 10.005, 102), (1, 10.005, 98)],
        )
        result = self.processor.process_request(request)
        self.assertIsNotNone(result.crossing_timestamp)


class TestRLRResultShapeExtra(RLRTestCase):
    """tests.md section 13 (remaining cases beyond slice 1)."""

    def test_malformed_request_raises_rather_than_returning_partial_result(self):
        request = make_request(car_id="", trajectory=[])
        with self.assertRaises(ValueError):
            self.processor.process_request(request)


if __name__ == "__main__":
    unittest.main()
