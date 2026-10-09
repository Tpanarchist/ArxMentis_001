import tempfile
import unittest
from pathlib import Path

from arxmentis import (
    dependent_transition,
    plastic_transition,
    read_state,
    write_state,
)


class DerivedCompositionTests(unittest.TestCase):
    def test_xor_then_plastic_is_a_gated_write(self) -> None:
        for driver_value in (0, 1):
            for target_value in (0, 1):
                for selector_value in (0, 1):
                    with self.subTest(
                        driver=driver_value,
                        target=target_value,
                        selector=selector_value,
                    ):
                        with tempfile.TemporaryDirectory() as directory:
                            root = Path(directory)
                            driver = root / "driver"
                            target = root / "target"
                            selector = root / "selector"
                            write_state(driver_value, driver)
                            write_state(target_value, target)
                            write_state(selector_value, selector)

                            dependent_transition(driver, target)
                            plastic_transition(driver, target, selector)

                            expected = (
                                driver_value
                                if selector_value == 1
                                else target_value
                            )
                            self.assertEqual(read_state(target), expected)
                            self.assertEqual(read_state(driver), driver_value)
                            self.assertEqual(read_state(selector), selector_value)


if __name__ == "__main__":
    unittest.main()
