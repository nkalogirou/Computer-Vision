import cv2
import mediapipe as mp
import serial

# Initialize Bluetooth connection
bluetooth_port = '/dev/tty.HC-06'  # Adjust to your specific Bluetooth port
baud_rate = 9600  # Standard baud rate
arduino = serial.Serial(bluetooth_port, baud_rate)

# Initialize the webcam to capture video
cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("Error: Webcam could not be opened.")
    exit()  # Exit if the webcam cannot be opened

# Set webcam frame size
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 600)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 500)

# Initialize MediaPipe for hand tracking
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
hand = mp_hands.Hands()

# Initialize accessibility mode to be off by default
accessibility_mode = False
# List to store specified fingers
specified_fingers = [] 
# Function to count extended fingers
def count_fingers(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Little
    finger_count = 0
   
    # Check if finger tips are above PIP joints (indicating extension)
    for i in range(1, 5):
        if hand_landmarks.landmark[tip_ids[i]].y < hand_landmarks.landmark[tip_ids[i] - 1].y:
            finger_count += 1
   
    # Check if the thumb is extended (for both left and right hands)
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[tip_ids[0] - 2].x:
        finger_count += 1

    return finger_count

# Function to detect which fingers are up in accesibility settings
def detect_fingers(hand_landmarks, specified_fingers):
    finger_count = []
    for finger in specified_fingers:
        if hand_landmarks.landmark[finger].y < hand_landmarks.landmark[finger - 2].y:
            finger_count.append(1)
        else:
            finger_count.append(0)
    return finger_count


# Main loop to capture video and process hand landmarks
while True:
    movement = 's'
    success, frame = cap.read()  # Read from webcam
    if success:
        # Convert the frame to RGB for MediaPipe
        RGB_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
       
        # Process the frame to get hand landmarks
        result = hand.process(RGB_frame)
       # Display accessibility mode status at the bottom left of the frame if enabled
        if accessibility_mode and result.multi_hand_landmarks:
            frame_height, frame_width = frame.shape[:2]
            accessibility_text = "Accessibility Mode: ON"
            cv2.putText(frame, accessibility_text, (10, frame_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            for hand_landmarks in result.multi_hand_landmarks:
                # Detect which fingers are up
                finger_count = detect_fingers(hand_landmarks,specified_fingers)
                # Display the detected fingers on the frame
                cv2.putText(frame, f'Fingers: {finger_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
               
                print("Fingers up:", finger_count)  # Debug output
                 # Determine the movement based on the finger array
                if finger_count == [1, 1] or finger_count == [1,1,1] or finger_count == [1,1,1,1]:
                    movement = 'F'
                    print("Forward")
                    arduino.write(movement.encode())
                elif finger_count == [0, 1] or finger_count == [0,1,1] or finger_count == [0,0,1,1]:
                    movement = 'r'
                    print("Right")
                    arduino.write(movement.encode())
                elif finger_count == [1, 0] or finger_count == [1,1,0] or finger_count == [1,1,0,0]:
                    movement = 'l'
                    print("Left")
                    arduino.write(movement.encode())
                elif finger_count == [0,1,0] or finger_count == [0,1,1,0]:
                    movement = 'b'
                    print("Backwards")
                    arduino.write(movement.encode())
                else:
                    movement = 's'
                    print("Stop")
                    arduino.write(movement.encode())

        # If hand landmarks are found, process them
        elif result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Draw the landmarks on the frame
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
               
                # Count extended fingers
                finger_count = count_fingers(hand_landmarks)
               
                # Determine hand side (left or right)
                if hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x < 0.5:
                    hand_side = "Right"
                    text_position = (frame.shape[1] - 180, 30)
                else:
                    hand_side = "Left"
                    text_position = (frame.shape[1] - 180, 30)
                # Display the counted finger on the frame
                cv2.putText(frame, f'Fingers: {finger_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

               
                # Display the counted finger and hand side on the frame
                cv2.putText(frame, f'{hand_side} Hand - Fingers: {finger_count}', text_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                 
                finger_count = count_fingers(hand_landmarks)
                print("Finger count:", finger_count)  # Debug output
                #if case for the data to be sent
                if(finger_count==5):
                    movement = 'F'
                    print("Forward\n")
                    arduino.write(movement.encode())
                elif(finger_count==4):
                    movement = 'f'
                    print("Forward Slower\n")
                    arduino.write(movement.encode())
                elif(finger_count==3):
                    movement = 'l'
                    print("Left\n")
                    arduino.write(movement.encode())
                elif(finger_count==2):
                    movement = 'r'
                    print("Right\n")
                    arduino.write(movement.encode())
                elif(finger_count==1):
                    movement = 'b'
                    print("Backwards\n")
                    arduino.write(movement.encode())
                else:
                    movement = "s"
                    print("Stop\n")
                    arduino.write(movement.encode())  

        else:
            movement = "s"
            print("Stop\n") 
            arduino.write(movement.encode())       
            #arduino.write(f"{finger_count}".encode())
                    
        # Show webcam output            
        cv2.imshow("Hand Tracking", frame)  

        key = cv2.waitKey(1)
        if key == ord('a'):
            accessibility_mode = not accessibility_mode
            print("Accessibility mode:", "On" if accessibility_mode else "Off")
            if accessibility_mode:
                num_fingers = int(input("Enter the number of fingers to use (max 4): "))
                specified_fingers = []
                if num_fingers > 4:
                    num_fingers = 4
                for _ in range(num_fingers):
                    finger = int(input("Enter finger index (4 for thumb, 8 for index, 12 for middle, 16 for ring, 20 for little): "))
                    if finger in[4,8,12,16,20]:
                        specified_fingers.append(finger)
        
        if key == ord('q'):  # Exit loop if 'q' is pressed
            break

# Cleanup resources
cap.release()  # Release the webcam
cv2.destroyAllWindows()  # Close OpenCV windows
arduino.close()  # Close the Bluetooth connection
