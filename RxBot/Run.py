from threading import Thread
from Initialize import *
initSetup()
from Resources import *


def main():
    print("Starting... go to the game tab")
    time.sleep(2)

    #resetStartAgain()
    while True:
        try:
            startRequest()
            resetStartAgain()

        except StopIteration as e:
            print("Error detected - Trying again.")
            print(e)
            resetStartAgain()



def tick():
    prevTime = datetime.datetime.now()
    while True:
        time.sleep(0.4)

        if misc.timerActive:  # If a timer IS ACTIVE, check the rest of this stuff. If not, ignore it.

            for timer in misc.timers:  # For each timer that is active...

                if datetime.datetime.now() > misc.timers[timer]:  # Check if the stored TARGET TIME of that timer is greater than the current time, now.

                    misc.timerDone(timer)  # If it is, call the timerdone function
                    break

        # Timers that send stuff every X seconds

        # if datetime.datetime.now() > prevTime + datetime.timedelta(minutes=settings["TIMER DELAY"]):
        #     chatConnection.sendToChat(resources.askChatAQuestion())
        #     prevTime = datetime.datetime.now()


if __name__ == "__main__":
    t1 = Thread(target=main)
    t2 = Thread(target=tick)

    t1.start()
    t2.start()

