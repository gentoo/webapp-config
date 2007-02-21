# Copyright 1999-2003 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /home/cvsroot/gentoo-x86/dev-db/phpmyadmin/phpmyadmin-2.5.4.ebuild,v 1.6 2003/12/15 20:03:27 stuart Exp $

inherit eutils
inherit webapp

MY_P=phpMyAdmin-${PV/_p/-pl}
DESCRIPTION="Web-based administration for MySQL database in PHP"
HOMEPAGE="http://phpmyadmin.sourceforge.net/"
SRC_URI="mirror://sourceforge/${PN}/${MY_P}-php.tar.bz2"
RESTRICT="nomirror"
LICENSE="GPL-2"
KEYWORDS="alpha arm ppc hppa mips sparc x86 amd64"
DEPEND=">=net-www/apache-1.3
	>=dev-db/mysql-3.21 <dev-db/mysql-5.0
	>=dev-php/mod_php-3.0.8
	sys-apps/findutils"
S=${WORKDIR}/${MY_P}

src_unpack() {
	unpack ${A}
	epatch ${FILESDIR}/config.inc.php-${PV}.patch

	# Remove .cvs* files and CVS directories
	find ${S} -name .cvs\* -or \( -type d -name CVS -prune \) | xargs rm -rf
}

src_compile() {
	einfo "Setting random user/password details for the controluser"

	local pmapass="${RANDOM}${RANDOM}${RANDOM}${RANDOM}"
	mv config.inc.php ${T}/config.inc.php
	sed -e "s/@pmapass@/${pmapass}/g" \
		${T}/config.inc.php > config.inc.php
	sed -e "s/@pmapass@/${pmapass}/g" \
		${FILESDIR}/mysql-setup.sql.in-${PV} > ${T}/mysql-setup.sql
}

src_install() {
	webapp_src_preinst

	local docs="ANNOUNCE.txt CREDITS Documentation.txt RELEASE-DATE-${PV} TODO ChangeLog LICENSE README"

	# install the SQL scripts available to us
	#
	# unfortunately, we do not have scripts to upgrade from older versions
	# these are things we need to add at a later date

	webapp_sqlscript mysql ${T}/mysql-setup.sql

	# handle documentation files
	#
	# NOTE that doc files go into /usr/share/doc as normal; they do NOT
	# get installed per vhost!

	dodoc ${docs}
	for doc in ${docs} INSTALL; do
		rm -f ${doc}
	done

	# Copy the app's main files
	
	einfo "Installing main files"
	cp -r . ${D}${MY_HTDOCSDIR}

	# Identify the configuration files that this app uses

	webapp_configfile ${MY_HTDOCSDIR}/config.inc.php

	# Identify any script files that need #! headers adding to run under
	# a CGI script (such as PHP/CGI)
	#
	# for phpmyadmin, we *assume* that all .php files that don't end in
	# .inc.php need to have CGI/BIN support added

	for x in `find . -name '*.php' -print | grep -v 'inc.php'` ; do
		webapp_runbycgibin php ${MY_HTDOCSDIR}/$x
	done

	# there are no files which need to be owned by the web server

	# add the post-installation instructions

	webapp_postinst_txt en ${FILESDIR}/postinstall-en.txt

	# all done
	#
	# now we let the eclass strut its stuff ;-)

	webapp_src_install
}
