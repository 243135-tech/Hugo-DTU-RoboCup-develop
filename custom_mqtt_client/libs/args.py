import argparse


class Args:
    def __init__(self):
        parser = argparse.ArgumentParser(description='HugoBoss MQTT client')

        # parser.add_argument('-w', '--white', action='store_true', help='Calibrate white tape level')
        parser.add_argument('-t', '--print-teensy-info', action='store_true', help='Print teensy info to console')
        parser.add_argument('-n', '--now', action='store_true', help='Start drive now (do not wait for start button)')
        parser.add_argument(
            '-l', 
            '--log-level', 
            type=str, 
            default="INFO", 
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
            help='Set the log level of loguru (default: INFO)'
        )

        self.args = parser.parse_args()
        if self.args.log_level != 'INFO':
            print(f"[+] Command line argument '--log_level'={self.args.log_level}")
            print("")


    def get(self, name):
        return getattr(self.args, name)

    def set(self, name, value):
        return setattr(self.args, name, value)


arg_parser = Args()