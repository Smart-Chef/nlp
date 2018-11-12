from SpeechRecognition_test import NLP

class TestCase:
    def __init__(self, _nlp, _command):
        self.nlp = _nlp
        self.command = _command
        self.passed = False
        self.nlp.annunciate(_command)
        self.execute_test()

    def execute_test(self):
        self.nlp.parse_command(self.command, True)


def main():
    test_nlp = NLP()

    choice = ""
    while choice != "X":
        print "Run a group of tests:"
        print "  A: Temp"
        print "  B: Weight"
        print "  C: Timer"
        print "  D: Recipe"
        print "  E: Misc"
        print "  F: Voice trial"
        print "  X: Exit"
        choice = raw_input("Selection: ")

        if choice == "A":
            # ------- TEMPERATURE ------- #
            test_value = 45
            test_nlp.chef.set_temp([test_value, " degrees F"])
            temp_tests = ["What is the oven temperature",
                          "How hot is the dish",
                          "Where's my heat at",
                          "What's the temperature"]
            for test_case in temp_tests:
                TestCase(test_nlp, test_case)

        elif choice == "B":
            # ------- WEIGHT ------- #
            test_value = 15
            test_nlp.chef.set_weight([test_value, " oz"])
            weight_tests = ["What is the dish weight",
                            "How heavy is the dish"]
            for test_case in weight_tests:
                TestCase(test_nlp, test_case)

        elif choice == "C":
            # ------- TIMER ------- #
            read_timer_tests = ["How much time is left",
                                "When will my dish be done",
                                "What time will my dish finish",
                                "What is the timer at"]
            for test_case in read_timer_tests:
                TestCase(test_nlp, test_case)

            set_timer_tests = ["Set timer for 3 hours and 45 minutes",
                               "Set timer for 2 and a half hours and 80 minutes",
                               "Set timer for seconds and three quarters minutes",
                               "Set timer for minutes",
                               "Set timer for hours",
                               "Set timer",
                               "Set alarm for 3 o'clock",
                               "Set alarm for 2:30"]
            for test_case in set_timer_tests:
                TestCase(test_nlp, test_case)

        elif choice == "D":
            # ------- RECIPE ------- #
            recipe_tests = ["Next step",
                            "Move to next step",
                            "Go to next step",
                            "What is the next step",
                            "Last step",
                            "Previous step",
                            "What do I need",
                            "What utensils do I need"]
            for test_case in recipe_tests:
                TestCase(test_nlp, test_case)

        elif choice == "E":
            # ------- MISCELLANEOUS ------- #
            misc_tests = ["Help me",
                          "How do you cook spaghetti",
                          "Find a video",
                          "What's the difference between sliced and chopped"]
            for test_case in misc_tests:
                TestCase(test_nlp, test_case)

        elif choice == "F":
            test_nlp.run_nlp()

main()