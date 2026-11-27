# Local builds (run on any machine with podman; ISO needs root)
image := "localhost/fedora-noctalia:latest"
fedora := "45"

build:
    podman build --build-arg FEDORA_VERSION={{fedora}} -t {{image}} .

# Rootful build, needed so bootc-image-builder can see the image
build-root:
    sudo podman build --build-arg FEDORA_VERSION={{fedora}} -t {{image}} .

iso: build-root
    mkdir -p output
    sudo podman run --rm -it --privileged --pull=newer \
        --security-opt label=type:unconfined_t \
        -v ./output:/output \
        -v /var/lib/containers/storage:/var/lib/containers/storage \
        -v ./iso/config.toml:/config.toml:ro \
        quay.io/centos-bootc/bootc-image-builder:latest \
        --type anaconda-iso --rootfs btrfs --chown $(id -u):$(id -g) \
        {{image}}
    @ls -lh output/bootiso/

# Check the Umbriel config without building (needs umbriel installed locally)
validate:
    XDG_CONFIG_HOME=/nonexistent XDG_CONFIG_DIRS=$PWD/system_files/etc/xdg umbriel config validate

# Poke around inside the built image
shell: build
    podman run --rm -it {{image}} bash
