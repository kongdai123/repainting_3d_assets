### Python 
##### Miniconda
I used miniconda for virtual environment 
follow the instructions here to install
```https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html```
##### Create environment, torch, and pytorch3d
```conda create -n 2nd_life_3d_assets python=3.9```\
```conda activate 2nd_life_3d_assets```\
```conda install pytorch=1.13.0 torchvision pytorch-cuda=11.6 -c pytorch -c nvidia```\
```conda install -c fvcore -c iopath -c conda-forge fvcore iopath```\
```conda install pytorch3d -c pytorch3d```
#### Install rest of the packages
run ```pip install -r requirements.txt``` to install rest of the packages

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