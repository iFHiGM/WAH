#!/usr/bin/env sh

set -e

[ "x${MSYSTEM}" != "xMINGW64" ] && echo "请打开MinGW64环境重新执行WAH！"

echo "-MINGW64环境正确！"

echo "-开始安装Emacs编译环境..."


function execute_command() {
    cmd=$(echo $1 | perl -nE 'print if s/\s+/ /g')

    is_skip=$2
    [ "$is_skip" = true ] && return

    echo -ne "Will exec cmd: \e[32m$cmd\e[0m\n"
    if [ "${IS_DRY_RUN}" = false ]; then
        (eval ${cmd})
    else
        echo -e "\e[33mDry run...\e[0m"
    fi
}

execute_command "pacman -Syyu"

# Install msys2 base libs.
execute_command "pacman -Syu --needed \
    filesystem \
    msys2-runtime \
    bash \
    libreadline \
    libiconv \
    libarchive \
    libgpgme \
    libcurl \
    pacman \
    ncurses \
    libintl"


# Install emacs build dependencies.
execute_command "pacman -Syu \
    base-devel \
    mingw-w64-x86_64-toolchain \
    mingw-w64-x86_64-xpm-nox \
    mingw-w64-x86_64-libtiff \
    mingw-w64-x86_64-giflib \
    mingw-w64-x86_64-jbigkit \
    mingw-w64-x86_64-libpng \
    mingw-w64-x86_64-libjpeg-turbo \
    mingw-w64-x86_64-librsvg \
    mingw-w64-x86_64-libxml2 \
    mingw-w64-x86_64-gnutls" true
# Or
execute_command "pacman -Su autoconf autogen automake automake-wrapper diffutils git guile texinfo libgc libguile libltdl libunistring  make mingw-w64-x86_64-binutils mingw-w64-x86_64-bzip2 mingw-w64-x86_64-cairo mingw-w64-x86_64-crt-git mingw-w64-x86_64-dbus mingw-w64-x86_64-expat mingw-w64-x86_64-fontconfig mingw-w64-x86_64-freetype mingw-w64-x86_64-gcc mingw-w64-x86_64-gcc-libs mingw-w64-x86_64-gdk-pixbuf2 mingw-w64-x86_64-gettext mingw-w64-x86_64-giflib mingw-w64-x86_64-glib2 mingw-w64-x86_64-gmp mingw-w64-x86_64-gnutls mingw-w64-x86_64-harfbuzz mingw-w64-x86_64-headers-git mingw-w64-x86_64-imagemagick mingw-w64-x86_64-isl mingw-w64-x86_64-libffi mingw-w64-x86_64-libgccjit mingw-w64-x86_64-libiconv  mingw-w64-x86_64-libjpeg-turbo mingw-w64-x86_64-libpng mingw-w64-x86_64-librsvg mingw-w64-x86_64-libtiff mingw-w64-x86_64-libwinpthread-git mingw-w64-x86_64-libxml2 mingw-w64-x86_64-mpc mingw-w64-x86_64-mpfr mingw-w64-x86_64-pango mingw-w64-x86_64-pixman mingw-w64-x86_64-winpthreads mingw-w64-x86_64-xpm-nox mingw-w64-x86_64-lcms2 mingw-w64-x86_64-xz mingw-w64-x86_64-zlib tar wget mingw-w64-x86_64-jansson pkgconf openssl nano" true

# external function dependencies.
additional_options=""
[ "${IS_INCLUDE_TREE_SITTER}" = true ] && {
    echo "包含tree-sitter编译！"
    additional_options="--with-tree-sitter"
    execute_command "pacman -Syu mingw-w64-x86_64-tree-sitter"
}

[ ! -d "${EMACS_SOURCE_PATH}" ] && {
    execute_command "git clone -b master git://git.sv.gnu.org/emacs.git '${EMACS_SOURCE_PATH}'"
}


# TODO: 需要验证必要性
# 配置git
execute_command "git config core.autocrlf false" true

execute_command "cd \"${EMACS_SOURCE_PATH}\" && \
    WANT_AUTOCONF=latest ./autogen.sh && \
    mkdir -p build && cd build && \
    PKG_CONFIG_PATH=/mingw64/lib/pkgconfig ../configure \
        --with-native-compilation \
        --with-gnutls --with-jpeg \
        --with-png \
        --with-rsvg \
        --with-tiff \
        --with-wide-int \
        --with-xft \
        --with-xml2 \
        --with-xpm \
        --without-dbus \
        --without-imagemagick \
        --without-pop \
        --with-json \
        --with-pgtk \
        ${additional_options} && \
    make -j$(($(nproc) + 1)) && \
    make install prefix=\"${EMACS_INSTALL_PATH}\""
