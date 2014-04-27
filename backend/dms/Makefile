# 
# Filename    : Makefile
# Description : Builds library
# Author      : David R Thompson, based on code by Ben Bornstein
# 
# Copyright 2012, by the California Institute of Technology. ALL RIGHTS 
# RESERVED. United States Government Sponsorship acknowledged. Any commercial 
# use must be negotiated with the Office of Technotc_write_logy Transfer at the 
# California Institute of Technology.  This software is controlled under the 
# U.S. Export Regulations and may not be released to foreign persons without 
# export authorization, e.g., a license, license exception or exemption.
#


# -----------------------------------------------------------------------------
# Variables
# -----------------------------------------------------------------------------

CC        ?= gcc
AR        ?= ar
RANLIB    ?= ranlib
DEBUG_CFLAGS   += -Wall -g -O2 -pg -DTC_LITTLE_ENDIAN
CFLAGS += -pg -fPIC -Wall -O2 -DTC_LITTLE_ENDIAN


objects = common.o dms.o 
sources = common.c dms.c 
headers = common.h dms.h
program = dmsmf
libs   = -lm
libdms = libdms.a
libcutest = cutest-1.5/libcutest.a

# -----------------------------------------------------------------------------
# Build Actions
# -----------------------------------------------------------------------------

.PHONY:  test 
all:  $(program) $(libdms) 

dmsmf:	$(objects) $(sources) $(headers) dmsmf.c
	${CC} $(CFLAGS) $(libs) -o dmsmf $(objects) dmsmf.c

$(libdms): $(objects)
	@echo
	@echo "--------------------------------------------------"
	@echo "Building library $(libdms)"
	@echo "--------------------------------------------------"
	$(AR) -cru $@ $(objects)
	$(RANLIB) $@

$(libcutest):
	$(MAKE) -w -C cutest-1.5

test: $(libcutest)  
	$(MAKE) -w -C test

coverity: $(program)
	@echo
	@echo "--------------------------------------------------"
	@echo "Running coverity"
	@echo "--------------------------------------------------"
	cov-build --dir coverity make distclean all install
	cov-analyze --dir coverity
	cov-format-errors --dir coverity -x -X

install:	$(program)
	@echo "installing to $(HOME)/bin"
	mkdir -p $(HOME)/bin
	cp $(program) $(HOME)/bin	

clean:
	/bin/rm -f *.o *.a 
	@if [ -d test ]; then $(MAKE) -w -C test $@; fi
	@if [ -d cutest-1.5 ]; then $(MAKE) -w -C cutest-1.5 $@; fi

distclean: clean
	/bin/rm -f $(library) $(program) $(tester)
	@if [ -d test       ]; then $(MAKE) -w -C test       $@; fi
	@if [ -d cutest-1.5 ]; then $(MAKE) -w -C cutest-1.5 $@; fi



# -----------------------------------------------------------------------------
# End
# -----------------------------------------------------------------------------

