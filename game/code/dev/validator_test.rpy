## dev/'s own test: the content check reports the planted mistakes (a missing
## label, a missing image and two files with the same image name). Run it
## from the test menu; the note says what was found.

label test_dev_validator:

    return dev.planted_check()
