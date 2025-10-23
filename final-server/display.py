import cv2
from multiprocessing import Queue

def start_display(frame_queue: Queue):

    try:
        while True:
            if not frame_queue.empty():
                frame = frame_queue.get()
                cv2.imshow("Received Video", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Display process exiting...")
    except Exception as e:
        print(f"Error in display thread: {e}")
    finally:
        frame_queue.close()
        cv2.destroyAllWindows()