import datetime
import multiprocessing

def producer(queue, message):
    """
    Producer function that sends messages to a queue to be consumed by the consumer.
    
    :param queue: The queue to which messages will be sent.
    :param messages: A string message.
    """
    print(datetime.datetime.now(), f"Producer is producing: {message}")
    queue.put(message)  # Put the message onto the queue

def consumer(queue, audio_consumer):
    """
    Consumer function that receives messages from a queue sent by the producer.
    
    :param queue: The queue from which messages will be received.
    """
    print(f"Initializing {audio_consumer}")
    audio_consumer.init()
    print(f"{audio_consumer} Initialized")
    while True:
        try:
            message = queue.get()  # Get the message from the queue
            producer(audio_consumer.queue, message)
            if message is None:
                print("Consumer received the sentinel value, stopping.")
                audio_consumer.process.join()
                break  # Sentinel value received, indicating the end of messages
            print(datetime.datetime.now(), f"Consumer is consuming: {message}")
        except KeyboardInterrupt:
            print("Get sure the child process ends")
            producer(audio_consumer.queue, None)
            audio_consumer.process.join()
            print("Ending cleanly")
