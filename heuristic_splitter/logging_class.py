

class LoggingClass:

    def __init__(self, logging_file):

        self.is_bdg_used = False
        self.is_bdg_new_used = False
        self.is_bdg_old_used = False

        self.is_lpopt_used = False

        self.grounding_strategy = ""

        self.bdg_used_for_rules = ""
        self.bdg_new_used_for_rules = ""
        self.bdg_old_used_for_rules = ""

        self.lpopt_used_for_rules = ""
        self.sota_used_for_rules = ""

        self.logging_file = logging_file

    def print_to_file(self):

        self.logging_file.write(f"--Lpopt-Used:{self.is_lpopt_used}\n")
        self.logging_file.write(f"--BDG-Used:{self.is_bdg_used}\n")
        self.logging_file.write(f"--BDG-New-Used:{self.is_bdg_new_used}\n")
        self.logging_file.write(f"--BDG-Old-Used:{self.is_bdg_old_used}\n")
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write(f"BDG-Is-Used-For-Rules:\n")
        self.logging_file.write("====================================\n")
        self.logging_file.write(self.bdg_used_for_rules)
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write(f"Lpopt-Is-Used-For-Rules:\n")
        self.logging_file.write("====================================\n")
        self.logging_file.write(self.lpopt_used_for_rules)
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write(f"SOTA-Is-Used-For-Rules:\n")
        self.logging_file.write("====================================\n")
        self.logging_file.write(self.sota_used_for_rules)
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write(f"New-BDG-Is-Used-For-Rules:\n")
        self.logging_file.write("====================================\n")
        self.logging_file.write(self.bdg_new_used_for_rules)
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write(f"Old-BDG-Is-Used-For-Rules:\n")
        self.logging_file.write("====================================\n")
        self.logging_file.write(self.bdg_old_used_for_rules)
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write(f"Final-Grounding-Strategy:\n")
        self.logging_file.write("====================================\n")
        self.logging_file.write(str(self.grounding_strategy))
        self.logging_file.write("\n------------------------------------\n")
        self.logging_file.write("\n")
