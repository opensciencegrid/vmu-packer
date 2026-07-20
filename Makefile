#!/usr/bin/make -f
NAME := vmu-packer
SPECFILE := rpm/$(NAME).spec
VERSION := $(shell rpm -q --qf '%{VERSION}\n' --specfile $(SPECFILE))
NAME_VERSION := $(NAME)-$(VERSION)
DATADIR := /usr/share/$(NAME)
BINDIR := /usr/bin
ETCDIR := /etc
UNITDIR := /usr/lib/systemd/system

SHELL:=bash


.PHONY: install
install: install-bin install-data install-systemd


.PHONY: install-bin
install-bin:
	mkdir -p $(DESTDIR)$(BINDIR)
	install -D -p -m 755 vmu-rebuild-one vmu-rebuild-all packer_arm_substitute.py vmu-packer-update $(DESTDIR)$(BINDIR)


.PHONY: install-systemd
install-systemd:
	mkdir -p $(DESTDIR)$(UNITDIR)
	install -p -m 644 systemd/vmu-packer-update.service systemd/vmu-packer-update.timer $(DESTDIR)$(UNITDIR)
	install -p -m 644 systemd/vmu-packer.service systemd/vmu-packer.timer $(DESTDIR)$(UNITDIR)


.PHONY: install-data
install-data:
	mkdir -p $(DESTDIR)$(DATADIR)
	install -p -m 644 packer-qemu.json $(DESTDIR)$(DATADIR)/packer-qemu.json
	for tmpl in $$(find . -name 'kickstart.ks' | cut -d '/' -f 2) files; do \
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
	osg-build rpmbuild -v --el9

.PHONY: kojiscratch
kojiscratch: testsource
	osg-build koji --scratch --getfiles --repo devops
