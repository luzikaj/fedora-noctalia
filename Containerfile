# Fedora Atomic spin: Umbriel compositor + Noctalia shell + Noctalia greeter
ARG FEDORA_VERSION=45
FROM quay.io/fedora/fedora-bootc:${FEDORA_VERSION}

# 1. Packages (Fedora + Terra). Scripts are bind-mounted, so they don't end up in the image.
RUN --mount=type=bind,source=build_files,target=/ctx \
    --mount=type=cache,target=/var/cache/libdnf5 \
    bash /ctx/build.sh

# 2. Config files: system defaults in /etc and /usr, your dotfiles in /etc/skel
COPY system_files/ /

# 3. Enable services, write the greetd config, validate the Umbriel config
RUN --mount=type=bind,source=build_files,target=/ctx \
    bash /ctx/finalize.sh

RUN bootc container lint
