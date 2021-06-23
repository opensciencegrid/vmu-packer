#!/usr/bin/make -f
NAME := vmu-packer
SPECFILE := rpm/$(NAME).spec
VERSION := $(shell rpm -q --qf '%{VERSION}\n' --specfile $(SPECFILE))
NAME_VERSION := $(NAME)-$(VERSION)
DATADIR := /usr/share/$(NAME)
BINDIR := /usr/bin
ETCDIR := /etc
TEMPLATES := centos_7 centos_8 centos_stream_8 sl_7

SHELL:=bash


.PHONY: install
install: install-bin install-data


.PHONY: install-bin
install-bin:
	mkdir -p $(DESTDIR)$(BINDIR)
	install -D -p -m 755 vmu-rebuild-one vmu-rebuild-all $(DESTDIR)$(BINDIR)


.PHONY: install-data
install-data:
	mkdir -p $(DESTDIR)$(DATADIR)
	install -p -m 644 packer-qemu.json $(DESTDIR)$(DATADIR)/packer-qemu.json
	for tmpl in $(TEMPLATES) files; do \
		mkdir -p $(DESTDIR)$(DATADIR)/$$tmpl; \
		install -p -m 644 $$tmpl/* $(DESTDIR)$(DATADIR)/$$tmpl; \
	done
	install -d -m 0700 $(DESTDIR)$(ETCDIR)/$(NAME)

.PHONY: testsource
testsource:
	mkdir -p upstream
	echo "type=git url=. name=$(NAME) tag=HEAD tarball=$(NAME_VERSION).tar.gz hash=$(HASH)" > upstream/test.source

.PHONY: rpmbuild
rpmbuild: testsource
	osg-build rpmbuild -v --el7

.PHONY: kojiscratch
kojiscratch: testsource
	osg-build koji --scratch --getfiles --repo devops
