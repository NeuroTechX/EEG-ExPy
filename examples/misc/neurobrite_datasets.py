print('Downloading 3 scikit-learn datasets')
import warnings
warnings.filterwarnings('ignore')
import numpy as np, os
from matplotlib import pyplot as plt
from sklearn import datasets

basedir = os.path.join(os.getcwd(),'stimulus_presentation/stim')

# olivetti faces
print('Downloading Olivetti faces')
stimdir = os.path.join(basedir, 'olivetti_faces')
try:
	os.makedirs(stimdir)
except:
	pass

faces = datasets.fetch_olivetti_faces()
images = faces.images

for i in range(np.shape(images)[0]):
    fig, ax = plt.subplots(1)
    plt.imshow(images[i,:,:], 'gray')
    plt.axis('off')
    ax.get_xaxis().set_visible(False) # this removes the ticks and numbers for x axis
    ax.get_yaxis().set_visible(False) # this removes the ticks and numbers for y axis
    plt.savefig(stimdir + '/image_' + str(i+1) + '.jpg',bbox_inches='tight',pad_inches=0)
    plt.close


# labelled faces in the wild
print('Downloading labelled faces in the wild')
stimdir = os.path.join(basedir,'faces_in_wild')
n_images = 200

try:
    os.makedirs(stimdir)
except:
    pass

faces = datasets.fetch_lfw_people()
images = faces.images

for i in range(n_images):
    fig, ax=plt.subplots(1)
    plt.imshow(images[i,:,:],'gray')
    plt.axis('off')
    ax.get_xaxis().set_visible(False) # this removes the ticks and numbers for x axis
    ax.get_yaxis().set_visible(False) # this removes the ticks and numbers for y axis
    plt.savefig(stimdir + '/image_' + str(i+1) + '.jpg',bbox_inches='tight',pad_inches=0)
    plt.close


# handwritten digits
print('Downloading digits data')
stimdir = os.path.join(basedir, 'digits')
n_images = 200

try:
    os.makedirs(stimdir)
except:
    pass

digits = datasets.load_digits()
images = digits.images
targets = digits.target

for i in range(n_images):
    fig, ax=plt.subplots(1)
    plt.imshow(images[i,:,:],'gray')
    plt.axis('off')
    ax.get_xaxis().set_visible(False) # this removes the ticks and numbers for x axis
    ax.get_yaxis().set_visible(False) # this removes the ticks and numbers for y axis
    plt.savefig(stimdir + '/image_' + str(i+1) + '_digit' + str(targets[i]) + '.jpg',bbox_inches='tight',pad_inches=0)
    plt.close


print('Done downloading all datasets')

