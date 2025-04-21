import winsound
from serial.tools import list_ports
import tkinter as tk
import threading

from utils import load_config, setup_logger
from eeg_headset import ThinkGear
from speller_board import SpellerBoardUI


def play_tone():
    """Plays a beep to indicate a blink was detected."""
    duration_ms = 200
    frequency_hz = 1000
    winsound.Beep(frequency_hz, duration_ms)


class BlinkDetector:
    def __init__(
        self,
        spike_threshold=500,
        dip_threshold=-400,
        baseline_threshold=150,
        max_dip_delay=500,
        max_baseline_delay=200
    ):
        self.spike_threshold = spike_threshold
        self.dip_threshold = dip_threshold
        self.baseline_threshold = baseline_threshold
        self.max_dip_delay = max_dip_delay
        self.max_baseline_delay = max_baseline_delay

        # State machine and sample history
        self.state = "IDLE"
        self.spike_index = None
        self.dip_index = None
        # self.sample_buffer = []  # Stores (index, value)
        self.current_index = 0

    def in_baseline(self, val):
        return -self.baseline_threshold < val < self.baseline_threshold

    def detect_blink(self, eeg_value):
        """
        Feed this function a stream of EEG values one-by-one.
        Returns True only when a full blink waveform is detected.
        """
        # self.sample_buffer.append((self.current_index, eeg_value))

        if self.state == "IDLE":
            if eeg_value > self.spike_threshold:
                self.spike_index = self.current_index
                self.state = "WAITING_FOR_DIP"

        elif self.state == "WAITING_FOR_DIP":
            if self.current_index - self.spike_index > self.max_dip_delay:
                self.state = "IDLE"  # too slow to find dip
            elif eeg_value < self.dip_threshold:
                self.dip_index = self.current_index
                self.state = "WAITING_FOR_BASELINE"

        elif self.state == "WAITING_FOR_BASELINE":
            if self.current_index - self.dip_index > self.max_baseline_delay:
                self.state = "IDLE"  # too slow to return to baseline
            elif self.in_baseline(eeg_value):
                self.state = "IDLE"
                return True  # Full blink waveform detected

        self.current_index += 1
        return False


def process_eeg_data(eeg_device: ThinkGear, blink_detector: BlinkDetector, ui: SpellerBoardUI):
    logger.info("Starting EEG data processing loop")
    try:
        while True:
            eeg_device.fetch_data()
            data = eeg_device.data
            if "eeg_raw" in data.keys():
                eeg_val = data["eeg_raw"]
                if blink_detector.detect_blink(eeg_val):
                    ui.on_blink_detected()
                    play_tone()
                    logger.info(
                        "Blink detected! Making character selection in UI!")
            elif "eeg_asic" in data.keys():
                logger.debug(eeg_device.data)
    except KeyboardInterrupt:
        logger.info("Stopping EEG data processing loop")
    finally:
        eeg_device.ser.close()
        ui.running = False
        logger.info("Closed EEG device connection due to keyboard interrupt")


def main():
    global config, logger
    config = load_config()
    if config["log_folder"] is None:
        logfile = None
    else:
        logfile = config["log_folder"] / "eeg_assistive_comm.log"
    logger = setup_logger(logfile)
    logger.info("Beginning execution")

    logger.info("Attempting to connect to EEG device")
    baud_rate = config["baud_rate"]
    if config["serial_port"]:
        logger.info(f"Using specified device: {config['serial_port']}")
        try:
            eeg_device = ThinkGear(config["serial_port"], baud_rate)
            logger.info(f"Connected to EEG device on {config['serial_port']}")
        except Exception as e:
            logger.error(f"Failed to connect to specified device: {e}")
            raise
    else:
        ports = list_ports.comports()[::-1]
        logger.info(
            f"Port not specified, found {len(ports)} available ports... attempting connection")
        eeg_device = None
        for port in ports:
            try:
                eeg_device = ThinkGear(port.device, baud_rate)
                logger.info(f"Connected to EEG device on {port.device}")
                break
            except Exception as e:
                logger.warning(f"Failed to connect to {port.device}: {e}")

        if eeg_device is None:
            logger.error(
                f"Failed to connect to any EEG device on available ports {', '.join([port.device for port in ports])}")
            raise

    # TODO: read eeg data in loop until proper electrode contact is made (signal=0)
    pass

    logger.info("Initializing BlinkDetector")
    blink_detector = BlinkDetector(
        spike_threshold=config["blink_spike_threshold"],
        dip_threshold=config["blink_dip_threshold"],
        baseline_threshold=config["blink_baseline_threshold"],
        max_dip_delay=config["blink_max_dip_delay"],
        max_baseline_delay=config["blink_max_baseline_delay"]
    )

    logger.info("Initializing SpellerBoardUI")
    root = tk.Tk()
    spellerboard_ui = SpellerBoardUI(root)

    # Start EEG reading in a separate thread
    threading.Thread(
        target=process_eeg_data,
        args=(
            eeg_device,
            blink_detector,
            spellerboard_ui
        ),
        daemon=True
    ).start()

    logger.info("Starting Speller Board UI main loop")
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info(
            "Stopping Speller Board UI main loop due to keyboard interrupt")

    logger.info("Ending program execution")


if __name__ == "__main__":
    main()
