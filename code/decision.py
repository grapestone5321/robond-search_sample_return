import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!
    
    # Example:
    # Check if we have vision data to make decisions with
    
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'
                          

            # Rover_stuck: When the rover get stuck in place, we need to decide what to do to help it move again
            if Rover.vel <= 0.3 and Rover.vel >= -0.3 and not Rover.is_stuck:
                if Rover.stuck_time_initial is None:
                    Rover.stuck_time_initial = Rover.total_time
                if ((Rover.total_time - Rover.stuck_time_initial) >= Rover.stuck_time_max_waiting):
                    Rover.is_stuck = True
            elif Rover.is_stuck:
                if Rover.vel >= 0.6 or Rover.vel <= -0.6:
                    # rover is stuck, but moving slowly. It seems that it can free itself, so it will no longer be "stuck"
                    Rover.is_stuck = False
                    Rover.stuck_time_initial = None
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                else:
                    # rover is stuck and not moving. We will try to make it go backwards
                    Rover.throttle = -Rover.throttle_set
                    Rover.brake = 0
                    Rover.steer = 0
                    if ((Rover.total_time - Rover.stuck_time_initial) // Rover.stuck_time_max_waiting) % 5 == 0:
                        Rover.throttle = 0
                        Rover.steer = np.clip(-(Rover.steer + 10), -15, 15)
                    if ((Rover.total_time - Rover.stuck_time_initial) // Rover.stuck_time_max_waiting) % 10 == 0:
                        Rover.throttle = Rover.throttle_set
            else:
                Rover.is_stuck = False
                Rover.stuck_time_initial = None


        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
        # Just to make the rover do something 
        # even if no modifications have been made to the code
        else:
            Rover.steer = 0
            Rover.brake = 0
        
        # If in a state where want to pickup a rock send pickup command
        if Rover.near_sample:
            if Rover.vel == 0:
                #rover is not moving: pick rock
                if not Rover.picking_up:
                    Rover.send_pickup = True
            else:
                #rover is moving: stop and pick rock
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
                Rover.mode = 'stop'
        # else: When the rover is not close to rock but there is some rock in the horizon, we try to guide it to go towards rock
        elif Rover.rock_angles is not None and len(Rover.rock_angles) >= Rover.rock_angles_detected:
            Rover.steer = np.clip(np.median(Rover.rock_angles * 180/np.pi), -15, 15)
            if Rover.vel >= 1:
                # stop
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.mode = 'stop'
            else:
                # moving toward the rock
                Rover.throttle = Rover.throttle_set
                Rover.brake = 0
                Rover.mode = 'forward'        
    
    return Rover

