name: Build APK

on:
  push:
    branches:
      - main
      - master

jobs:
  build:

    runs-on: ubuntu-latest

    steps:

    - name: Checkout
      uses: actions/checkout@v4


    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.10"


    - name: Install Linux Dependencies
      run: |
        sudo apt-get update

        sudo apt-get install -y \
          git \
          zip \
          unzip \
          openjdk-17-jdk \
          build-essential \
          python3-dev \
          python3-pip \
          autoconf \
          libtool \
          pkg-config \
          zlib1g-dev \
          libffi-dev \
          libssl-dev \
          cmake


    - name: Setup Android SDK
      uses: android-actions/setup-android@v3


    - name: Install Android Packages
      run: |
        yes | sdkmanager --licenses || true

        sdkmanager \
        "platform-tools" \
        "platforms;android-33" \
        "build-tools;33.0.2"


    - name: Install Buildozer
      run: |
        python -m pip install --upgrade pip
        pip install setuptools wheel
        pip install buildozer==1.5.0
        pip install cython==0.29.36


    - name: Build APK
      run: |
        rm -rf .buildozer
        buildozer -v android debug


    - name: Upload APK
      uses: actions/upload-artifact@v4
      with:
        name: Quant-Pro-Mobile-APK
        path: bin/*.apk
