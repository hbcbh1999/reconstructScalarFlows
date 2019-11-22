# reconstructScalarFlows

This is the code accompanying the ScalarFlow data set https://ge.in.tum.de/publications/2019-scalarflow-eckert/.
This code contains sources capture real-world scalar flow phenomena,
i.e. calibrate cameras, control and record smoke plumes, post-process captured videos, 
reconstruct 3D density and 3D velocity from the 2D captured images, and post-process the reconstructed quantities. 
The reconstruction code is embedded in the mantaflow framework http://mantaflow.com/.

Below you can find instructions for compiling and running the code.
First, install required software for mantaflow. Detailed instructions on how to compile and run mantaflow can be found at:
http://www.mantaflow.com/install.html and http://www.mantaflow.com/quickstart.html.
Then, clone the repository 'git clone https://bitbucket.org/marylen/reconstructscalarflows.git',
go to repository,
create build folder 'mkdir build',
go to build folder 'cd build'
build project 'cmake .. -DOPENMP=ON ,-DNUMPY='ON'',
and make project 'make -j4'.
If any errors occur, check the installation instructions for mantaflow.

Next, download a test data set from ScalarFlow, e.g., a single
tar file. You can request the download link here: https://forms.gle/ooPFuiMwYYE8TC1X6

The python scripts require several packages such as: numpy, matplotlib, scipy, opencv-python, picamera.
Please install them where required.

The detailed instructions of how to use the scripts are given in the scripts themselves. 
1. Use scenes/simpleplume.py to create a synthetic smoke plume and render synthetic images based on real-world camera calibration with renderVol.py.
2. Use extractPostprocess.py to post-process captured video streams of real-world smoke plumes. 
3. Use reconDenVel.py to reconstruct 3D density and velocity from the extracted 2D real-world capture images. 
4. Use postprocessRecons.py to cut off the inflow area from density, images, and velocity, and to create statistics (min, max, mean, and standard deviation for density, velocity, and images, and PSNR on image differences).

The scenes in the folder scenes/capture are not related to mantaflow, but are used to control the physical capture of the smoke plumes. The scripts are executed on the host computer controlling the physical capturing setup or on the Raspberry Pis controlling the cameras, servo motors, or smoke machine. 
These scripts were mostly developed by Daniel Frejek in his Bachelor's thesis "Optical Capture of Flow Data Utilizing Raspberry Pis" and guided research project "Improving a Low-Cost Capturing Process for Reconstructing Volume and Motion of Real Fluid Phenomena" and extended in the student's theses: “Experimental Capture of Smoke and Evaluation of Volume Reconstruction Algorithms” by Florian Reichhold and “Capturing Real Fluid Phenomena with Raspberry Pi Cameras” by Florian Alkofer.

## Details
### Physical Capturing
Details for our hardware setup can be found here https://ge.in.tum.de/publications/2019-scalarflow-eckert/. Our
smoke machine technically produces fog as it diffuses water with propylene glycol. But as the underlying physics of smoke and fog are equivalent, we refer to the visible tracers as smoke. 
We record the smoke with five camera modules mounted on Raspberry Pi computers named cam1 to cam5. The slide for moving the marker and the servo motors for controlling the top and bottom valves are steered through the sixth Raspberry Pi named motor. The smoke machine is controlled by the seventh Raspberry Pi smoky.
We connect with a host computer to the Raspberry Pis via ssh keys. The scripts we used are under scenes/capture.
#### Start
Switch on the camera and motor Raspberry Pis as well as the lights. To heat up the box and to put the smoke generation into operation, set the safety timer to a desired time span, e.g., 15 minutes, by pressing the green button for one second. The target temperature can be adjusted. It is usually set to 33.5C, but the actual temperature is often a bit higher: ~35C. Now, mount the Raspberry Pi computers for easy access to their SD card storage and start the host by calling ./01_mount_pis.sh and ./capturehost.py, respectively. The motor Pi will automatically connect to the host. In order to connect the camera Pis to the host, run ./02_startCaptureOrStream.sh 1. To verify the position and orientation of the cameras, sample images can be taken by typing ’s’ in the host command window. Sample images are taken, assembled, and displayed next to each other to monitor the camera’s field of views. Make sure that the smoke release is in the center and at a similar level of height for each camera. With the sample images, it is also possible to verify that the smoke is illuminated evenly for all camera angles. The images by the outer cameras are typically brighter, but it is best to reduce the differences in brightness over the camera views as much as possible.
#### Calibration
In order to calibrate the cameras, the black molton cloth needs to be lifted, such that the marker is visible and can move freely along the slide. To do so, the cloth is attached to the movable walls with the black-orange clips. Take a sample image for each camera to verify that each camera is able to see the marker. For calibration, use the regular room light, not the three diffuser lights. When position and orientation of the cameras are adjusted correctly, camera calibration is conducted by typing ’cal calib20190813’ in the host command window, where the second parameter is the calibration folder name, which is calib20190813 in this example. Now, the marker moves to twenty-one different positions, holds for five seconds, and the cameras take images. The marker returns home afterwards. These images are used to calculate the pixel’s rays, which takes place in background and also takes approximately one hour. The resulting ray calculations are 1_rays.txt to 5_rays.txt, which are later input to the reconstruction algorithm. To verify accurate calibration, the world-space ray directions are encoded in RGB values in 1_dir.png to 5_dir.png. The corresponding errors are displayed in 1_err.png to 5_err.png. Good calibration is recognized by smooth images of ray directions and very dark error images. If the rays need to be recalculated from a given set of images, the following command used: ./calibration/process_images.sh calibFolder –ed=1000, where 'ed' specifies the range into which the ray directions should be extrapolated into. If set to zero, no extrapolation takes place. The script process_image_stack.cpp in scenes/capture/calibration contains the code for calculating the rays. When changes are made, the script needs to be rebuilt by calling ./build.sh.
#### Recording
For recording, switch off the regular room light and switch on the three diffuser lights. Cover the marker and the box with the black molton cloth. We automated and simplified the smoke generation and recording process. An example command for recording smoke plumes is ’c 0813 80 10 6 3’, which is typed into the host command window, where ’c’ stands for capture, ’0813’ is the folder name’s prefix, ’80’ specifies how much percentage the bottom valve should be opened (the top valve is always fully opened), ’10’ determines how many captures should be taken, and ’6’ and ’3’ are the amounts of seconds the smoke machine pushes smoke into the box when initiating the sequence of captures or during the iteration of producing new captures. Smoke plumes are now automatically created and recorded where we explain the internal processes in the following. First, the valves are closed and smoke is filled into the box. Internally, the script ./servocontrol.sh is called with the argument ’fill’, which specifies to open both valves to 0 percentage, i.e., closes the valves. The script ./fillBox.sh is called with the argument of how many seconds the smoke machine should push smoke into the box, which is ’6’ in our example. Here, the script controlSmoke.py is used to communicate with the Raspberry Pi smoky. We wait 150 seconds until the spurious smoke has diffused and ambient air motions have calmed down. Then, for each of the ’10’ captures, we start recording, wait 5 seconds, and open the top and bottom valves by calling the script ./servocontrol.sh with the arguments ’plume’ and the percentage for opening the bottom valve, i.e., ’80’ in our example. We record the plume for another 18 seconds. Then, recording is stopped, the valves are closed, and the final folder name is created by adding a suffix ’_%s_%04d’ % (percentageLower, i) to the folder name’s prefix, which is ’0813’ in our example, where percentageLower is ’80’ and i is the number of the current capture. The folder names in our example are hence 0813_80_0000, 0813_80_0001, and so forth. The h264 videos are downloaded from the Raspberry Pi computers, converted to mp4, and stored in the current capture folder by calling the script ./grabVideos.sh. If more captures are about to be taken, we wait 60 seconds, ensure the valves are still closed, fill the box with the specified amount of smoke, i.e., by pressing the smoke machine’s button for ’3’ seconds in our example, and wait for 180 seconds until any spurious smoke has disappeared. Then, we continue with the capture as described in the previous paragraph. The code and script calls for capturing is found in capturehost.py from line 456 on.
### Post-Processing Captures
The raw camera images are post-processed in terms of extracting single frames from the videos, denoising the images, subtracting the background, and thresholding. Then, both raw and post-processed images (five per time step for each) are assembled into 3D numpy arrays, such that they follow mantaflow convention with shape=[z, y, x, 1], which is shape=[numberOfAngles, height, width, 1] in the case of images. The images are visualized with grayscale or color through matplotlib for raw and post-processed images, respectively. Visualization of images is conducted in function draw2DDensityNpy(...) in the script _visualize.py. Assembling and visualization is referred to as preparing the images for reconstruction input. The script for post-processing is scenes/reconstruct/extractPostprocess.py. The arguments to pass are the path of the capture, e.g., pathToCaptures/0813_80_0000, the number of cameras, i.e., 5 in our case, and three parameters determining which parts of post-processing should be executed. The three parameters and their default values are (prepImages, assembleUnproc, onlyPrep) = (True, True, False). prepImages determines if the images should be assembled to numpy arrays and visualized. assembleUnproc specifies if the raw input images should be assembled and visualized as well, or if only post-processed images should be handled. The last parameter onlyPrep specifies if only assembling and visualizing should take place (and no post-processing itself). This can be useful if images need to be re-visualized. Denoising and preparing the images takes the longest, where preparing the images is more time consuming than denoising.
### Reconstruct 
After post-processing the recorded images, we can start reconstructing 3D density and velocity from these 2D real-world images. Depending on which computer or server the reconstructions are run, it might make sense to reduce the number of used threads, e.g., by setting export OMP_NUM_THREADS=4. Using too many threads slows down run time. Reconstruction is started by calling the script scenes/reconstruct/reconDenVel.py. The parameters to pass are calibFolder, captureFolder, x-resolution, scaling factor, density smoothness, density kinetic penalty, velocity smoothness, velocity kinetic penalty, inflow smoothness, inflow kinetic penalty, inflow velocity. An example call is the following when called from build/: ./manta ../scenes/reconstruct/reconDenVel.py calib20190813 0813_80_0085 100 3 8 5e-2 5e-4 5e-1 5e-2 1e-4 1e-3 0.8, where ’calib20190813’ is the calibFolder, ’0813_80_0085’ is the captureFolder, ’100’ is the domain’s resolution in the x-direction, ’3’ specifies that there is no ground truth available, the input images are scaled by the factor ’8’, followed by the regularizing weights for smoothness and kinetic penalties, and the inflow velocity. If the reconstruction features small density explosions, you need to adjust the parameters, e.g., reduce the density’s and inflow’s smoothness weights. It is also important to scale the input images accordingly, such that all reconstructions lie in a similar range of density and velocity values. The output folder is a combination of prefix (chose some name that you like) and a suffix, where the input parameters are merged into a string. For each reconstruction, a .json file is written containing the most important parameters. If the cameras’ arrangement changes a lot, it might be necessary to adjust the reconstruction domain in source/plugin/ray.cpp. Here, the variables Ray::factorY, Ray::markerWidth, Ray::volWidthMeter, Ray::volOffset can be adjusted. To test the transformation from real-world to reconstruction domain and also to test the source placement, the lines following line 211 in reconDenVel.py can be used. Uncomment lines 214-215 and add ’, 10, False, src0’ to line 213 as written in the comment. Then, you will see a source placed in the reconstruction domain, which is a box specified by p0 and p1.
### Post-Processing Reconstructions 
The reconstructions are post-process for cutting off the inflow area (lower 15 cells if parameter of 7 is passed), coherent visualization, calculating the PSNR value of the image difference between input and rendered reconstructed density, and min, max, mean, standard deviation, and percentage of non-zero cells for density, velocity, and images. These steps are conducted in the script scenes/reconstruct/postprocessRecons.py. The parameters are captureFolder, cutOffCells, overwrite, saveNpz, visualize, visualizeVelocities, calcPSNR, calcStats, where an example call is as follows ./manta ../scenes/reconstruct/postprocessRecons.py 0813_80_0085/ 7 1 1 1 1 1 1. The parameter cutOffCells determines how many cells should be cut above the inflow area. The remaining parameters should be True by default. If global statistics are desired and global mean values are available, adapt meanDenGlobal, meanVelGlobal, and meanImgsGlobal to obtain unscaled and squared devDenGlobal, devVelGlobal, and devImgsGlobal.
### Summary
1. Mount Pis with ./01\_mount\_pis.sh, start host with ./capturehost.py, and connect clients ./02\_startCaptureOrStream.sh 1 (different command window).
2. Arrange cameras by taking sample images 's'.
3. Calibrate: remove cloth, use regular room light, type 'cal calibFolder' in host window
4. Record: put cloth back down, use three diffuser lights, ensure heating and smoke machine in operation (timer set to sufficient duration), sample images with 's' to verify arrangement: type 'c recordFolderPrefix percentageLower numberOfCaps secondsSmokeInit secondsSmokeIteration' (e.g., 'c 0813 80 10 6 3') in host window.
5. Post-process: call ./scenes/reconstruct/extractPostprocess.py pathToCaptures/captureFolder/ 5 1 1 0 for each captureFolder.
6. Reconstruct: call ./manta ../scenes/reconstruct/reconDenVel.py calibFolder captureFolder 100 3 8 5e-2 5e-4 5e-1 5e-2 1e-4 1e-3 0.8
7. Post-process reconstructions: call ./manta ../scenes/reconstruct/postprocessRecons.py captureFolder 7 0 1 1 1 1 1.