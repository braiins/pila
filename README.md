# Overview

**PILA** is a tool for SCons that simplifies building projects targetted
mostly for bare metal embedded systems that require integrating a lot of 3rd party
libraries with minimum effort. In addition it provides integration with
**Kconfig** frontend to allow configurable builds similar to how Linux
kernel or OpenWrt is being built. As a bonus feature, the tool allows
generating CMakeLists files that describe the built process almost 1:1. This
can be used by IDE's that are able to parse CMakeLists and provide thus full
code completion, source code navigation and all the nice features provided by
 powerful IDE's. At the same time it is possible to use the generated
 CMakeLists file for building the image.

Summary:

- a full featured scons tool
- support for **Kconfig** frontend
- optional geration of CMakeLists files for development in IDE's like CLion

# Provided Builders and Methods

## Builders
Generally all provided builders take an additional parameter (```is_enabled```)
that determines whether the builder is to be part of the current build.

### FeatureObject
Similar to [Object](http://www.scons.org/doc/HTML/scons-user/ch02s02.html).

The example builds a set of driver modules that consists of a main platform
module and conditionally built timer instances enabled in the current
configuration:
```
env.FeatureObject(source=['timer--platform.c'])

# Timer 1-14 support
for i in range(1, 15):
    env.FeatureObject(source=['timer_%d.c' %i],
		       is_enabled=getattr(env['CONFIG'], 'FREERTOS_DRIVERS_TIMER_%s' % i))
```

### BuiltInObject
This builder has no counter part in SCons. It is used to collect all feature
objects into 1 relatively linked object file (named ```built-in.o```) at the
level where the current SConscript is nested. The motivation is to simplify
the link step where only a few top-level built-in objects are being collected
. This idea has been borrowed from Linux kernel build system. Example of a
SConscript in a nested project:
```
import os

Import('env')

lora_env = env.Clone()
Export('lora_env')


env.FeatureSConscript(dirs=['Utilities'],
		      exports={'env': lora_env})

# built-in object that contains the entire LoRa stack -> register it into the
# toplevel environment for further linking
lora_env.BuiltInObject(env)
```

### ComponentProgram
Similar to [Program](http://www.scons.org/doc/HTML/scons-user/ch03s07.html),
however this variant takes all built-in objects registered in the current
build environment and links them into one binary.

```
env.ComponentProgram('firmware.elf')
```

## Environment Methods
### FeatureSConscript
This example calls sub-sconscripts in the the specified directories as long
as ```FREERTOS_DRIVERS_ADC``` feature is set.
```
env.FeatureSConscript(dirs=['adc'],
		      is_enabled=env['CONFIG'].FREERTOS_DRIVERS_ADC)
```
### LoadBuildEnv
### LoadProject
### ProjectSConscript

# CMake Autogen
CMakeLists autogeneration is controlled by ```TSR_ENABLE_CMAKE_GEN```
construction varabile. When enabled, each ```ComponentProgram``` produced by
the build system will be accompanied by a CMakeLists file. The name
of the file is: ```{TARGET}.CMakeLists.txt```, where ```{TARGET}``` is the
target name of the ```ComponentProgram```.
