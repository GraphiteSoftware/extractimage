#!/bin/bash

#IMAGE_SOURCE_DIR=/mnt/Software/Device/requested/R5.3-ss4-dev-405/
IMAGE_SOURCE_DIR=/mnt/Software/Device/nightly/sscloud-nougat-1183/
#IMAGE_SOURCE_DIR=/mnt/Software/Device/requested/R5.3-ss4-dev-404/
SYSTEM_DIR="system"
SYSTEM_FACT_DIR="system.factory"

export PATH=$PATH:~/tools/extract_img/

function validate()
{
    echo "Validating $IMAGE_SOURCE_DIR"
    if [ ! -d $IMAGE_SOURCE_DIR ];then
	echo "$IMAGE_SOURCE_DIR not exist, abort..."
        exit 1
    fi
    if [ -d $SYSTEM_DIR ];then
	echo "$SYSTEM_DIR exist, remove it"
        rm -rf $SYSTEM_DIR
    fi

    if [ -d $SYSTEM_FACT_DIR ];then
	echo "$SYSTEM_FACT_DIR exist, remove it"
        rm -rf  $SYSTEM_FACT_DIR
    fi
}

function prepare()
{
    echo "removing ./tmp ./system.img, $IMAGE_SOURCE_DIR/system"
    rm -rf ./tmp ./system.img $IMAGE_SOURCE_DIR/system
    mkdir ./tmp
    unzip $IMAGE_SOURCE_DIR/aosp_*-img*.zip -d ./tmp/
    #unzip $IMAGE_SOURCE_DIR/aosp_bullhead-img-1183-userdebug-0fd2a29f.zip -d ./tmp/
}

function extract_image()
{
    echo "Extracting image..."
    simg2img ./tmp/system.img system.full.img
    mkdir system.mnt
    mkdir system.factory
    sudo mount -n -o loop system.full.img system.mnt
    sudo cp -r system.mnt/* system.factory
    sudo umount -n system.mnt
    sudo chown -R ${USER}. system.factory
    rmdir system.mnt
    rm -r system.full.img
    ln -s system.factory system
}

function deliver()
{
    echo "About to deliver"
    mkdir -p $IMAGE_SOURCE_DIR/system/app
    mkdir -p $IMAGE_SOURCE_DIR/system/priv-app
    cp -rf ./system/app/SpacesPolicyApp $IMAGE_SOURCE_DIR/system/app/
    cp -rf ./system/app/SSCMService $IMAGE_SOURCE_DIR/system/app/
    cp -rf ./system/app/SpacesCore $IMAGE_SOURCE_DIR/system/app/
    cp -rf ./system/priv-app/SpacesManagerService $IMAGE_SOURCE_DIR/system/priv-app/
}

validate
prepare
extract_image
deliver
