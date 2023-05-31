### Installing instant-ngp
#### Source Code
Download instant-ngp
```git clone --recursive https://github.com/nvlabs/instant-ngp``` \
Reset to October repo (newest version does not run) \
```git reset --hard 54aba7cfbeaf6a60f29469a9938485bebeba24c3``` \
Go to ```dependencies/tiny-cuda-nn/include/tiny-cuda-nn/encodings``` \
and change the ```grid.h``` file to the new version in the file in ```nerf_recon/ngp_files/grid.h``` \

#### Compile
Log on to a session with GPU access, preferably the same GPU used to run the code\
Generate build files \
```cmake  . -B build -DNGP_BUILD_WITH_GUI=OFF```\
if there is an error regarding cmake version download the latest cmake binaries here \
https://github.com/Kitware/CMake/releases/download/v3.25.2/cmake-3.25.2-linux-x86_64.tar.gz \
Compile \
```cmake --build build --config RelWithDebInfo -j 16``` \
Go to ```nerf_recon/common.py``` in the REPO folder, not the instant-ngp folder \
Change the ```PAPER_FOLDER``` varible of line 24 to the instant-ngp directory


#### Network
Copy the NGP network config ```nerf_recon/ngp_files/fine_network.json``` to the Instant NGP config folder ```configs/nerf/```