FROM kalledk/dockerbase:centos7

MAINTAINER Kalle R. Møller

RUN yum install -y http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-0.5.3-1.el7.rf.x86_64.rpm \
	&& yum install -y curl createrepo mkisofs gzip coreutils xorriso \
	&& yum clean all -y
