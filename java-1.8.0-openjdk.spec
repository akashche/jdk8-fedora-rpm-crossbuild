# note, parametrised macros are order-senisitve (unlike not-parametrized) even with normal macros
# also necessary when passing it as parameter other macros. If not macro, then it is considered as switch
%global debug_suffix_unquoted -debug
# quoted one for shell operations
%global debug_suffix "%{debug_suffix_unquoted}"
%global normal_suffix ""

#if you wont only debug build, but providing java, build only normal build, but  set normalbuild_parameter
%global debugbuild_parameter  slowdebug
%global normalbuild_parameter release
%global debug_warning This package have full debug on. Install only in need, and remove asap.
%global debug_on with full debug on
%global for_debug for packages with debug on

# by default we build normal build always.
%global include_normal_build 1
%if %{include_normal_build}
%global build_loop1 %{normal_suffix}
%else
%global build_loop1 %{nil}
%endif

%global aarch64         aarch64 arm64 armv8
# sometimes we need to distinguish big and little endian PPC64
%global ppc64le         ppc64le
%global ppc64be         ppc64 ppc64p7
%global multilib_arches %{power64} sparc64 x86_64
%global jit_arches      %{ix86} x86_64 sparcv9 sparc64 %{aarch64} %{power64}

# By default, we build a debug build during main build on JIT architectures
%ifarch %{jit_arches}
%global include_debug_build 1
%else
%global include_debug_build 0
%endif

# On x86_64 and AArch64, we use the Shenandoah HotSpot
%ifarch x86_64 %{aarch64}
%global use_shenandoah_hotspot 1
%else
%global use_shenandoah_hotspot 0
%endif

%if %{include_debug_build}
%global build_loop2 %{debug_suffix}
%else
%global build_loop2 %{nil}
%endif

# if you disable both builds, then build fails
%global build_loop  %{build_loop1} %{build_loop2}
# note, that order  normal_suffix debug_suffix, in case of both enabled,
# is expected in one single case at the end of build
%global rev_build_loop  %{build_loop2} %{build_loop1}

%ifarch %{jit_arches}
%global bootstrap_build 1
%else
%global bootstrap_build 1
%endif

%if %{bootstrap_build}
%global targets bootcycle-images docs
%else
%global targets all
%endif

%ifnarch %{jit_arches}
# Disable hardened build on non-jit arches. Work-around for RHBZ#1290936.
%undefine _hardened_build
%global ourcppflags %{nil}
%global ourldflags %{nil}
%else
%ifarch %{aarch64}
# Disable hardened build on AArch64 as it didn't bootcycle
%undefine _hardened_build
%global ourcppflags "-fstack-protector-strong"
%global ourldflags %{nil}
%else
# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimisation of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wformat (required by -Werror=format-security) and -Wno-cpp to avoid FORTIFY_SOURCE warnings
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%global ourflags %(echo %optflags | sed -e 's|-Wall|-Wformat -Wno-cpp|' | sed -r -e 's|-O[0-9]*||')
%global ourcppflags %(echo %ourflags | sed -e 's|-fexceptions||')
%global ourldflags %{__global_ldflags}
%endif
%endif

# With diabled nss is NSS deactivated, so in NSS_LIBDIR can be wrong path
# the initialisation must be here. LAter the pkg-connfig have bugy behaviour
#looks liekopenjdk RPM specific bug
# Always set this so the nss.cfg file is not broken
%global NSS_LIBDIR %(pkg-config --variable=libdir nss)
%global NSS_LIBS %(pkg-config --libs nss)
%global NSS_CFLAGS %(pkg-config --cflags nss-softokn)
# see https://bugzilla.redhat.com/show_bug.cgi?id=1332456
%global NSSSOFTOKN_BUILDTIME_NUMBER %(pkg-config --modversion nss-softokn || : )
%global NSS_BUILDTIME_NUMBER %(pkg-config --modversion nss || : )
#this is worakround for processing of requires during srpm creation
%global NSSSOFTOKN_BUILDTIME_VERSION %(if [ "x%{NSSSOFTOKN_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSSSOFTOKN_BUILDTIME_NUMBER}" ;fi)
%global NSS_BUILDTIME_VERSION %(if [ "x%{NSS_BUILDTIME_NUMBER}" == "x" ] ; then echo "" ;else echo ">= %{NSS_BUILDTIME_NUMBER}" ;fi)


# fix for https://bugzilla.redhat.com/show_bug.cgi?id=1111349
%global _privatelibs libmawt[.]so.*
%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

# In some cases, the arch used by the JDK does
# not match _arch.
# Also, in some cases, the machine name used by SystemTap
# does not match that given by _build_cpu
%ifarch x86_64
%global archinstall amd64
%global stapinstall x86_64
%endif
%ifarch ppc
%global archinstall ppc
%global stapinstall powerpc
%endif
%ifarch %{ppc64be}
%global archinstall ppc64
%global stapinstall powerpc
%endif
%ifarch %{ppc64le}
%global archinstall ppc64le
%global stapinstall powerpc
%endif
%ifarch %{ix86}
%global archinstall i386
%global stapinstall i386
%endif
%ifarch ia64
%global archinstall ia64
%global stapinstall ia64
%endif
%ifarch s390
%global archinstall s390
%global stapinstall s390
%endif
%ifarch s390x
%global archinstall s390x
%global stapinstall s390
%endif
%ifarch %{arm}
%global archinstall arm
%global stapinstall arm
%endif
%ifarch %{aarch64}
%global archinstall aarch64
%global stapinstall arm64
%endif
# 32 bit sparc, optimized for v9
%ifarch sparcv9
%global archinstall sparc
%global stapinstall %{_build_cpu}
%endif
# 64 bit sparc
%ifarch sparc64
%global archinstall sparcv9
%global stapinstall %{_build_cpu}
%endif
%ifnarch %{jit_arches}
%global archinstall %{_arch}
%endif

%ifarch %{jit_arches}
%global with_systemtap 1
%else
%global with_systemtap 0
%endif

%ifarch %{ix86} x86_64
%global with_openjfx_binding 1
%global openjfx_path %{_jvmdir}/openjfx
# links src directories
%global jfx_jre_libs_dir %{openjfx_path}/rt/lib
%global jfx_jre_native_dir %{jfx_jre_libs_dir}/%{archinstall}
%global jfx_sdk_libs_dir %{openjfx_path}/lib
%global jfx_sdk_bins_dir %{openjfx_path}/bin
%global jfx_jre_exts_dir %{jfx_jre_libs_dir}/ext
# links src files
# maybe depend on jfx and generate the lists in build time? Yes, bad idea to inlcude cyclic depndenci, but this list is aweful
%global jfx_jre_libs jfxswt.jar javafx.properties
%global jfx_jre_native libprism_es2.so libprism_common.so libjavafx_font.so libdecora_sse.so libjavafx_font_freetype.so libprism_sw.so libjavafx_font_pango.so libglass.so libjavafx_iio.so
%global jfx_sdk_libs javafx-mx.jar packager.jar ant-javafx.jar
%global jfx_sdk_bins javafxpackager javapackager
%global jfx_jre_exts jfxrt.jar
%else
%global with_openjfx_binding 0
%endif

# Convert an absolute path to a relative path.  Each symbolic link is
# specified relative to the directory in which it is installed so that
# it will resolve properly within chrooted installations.
%global script 'use File::Spec; print File::Spec->abs2rel($ARGV[0], $ARGV[1])'
%global abs2rel %{__perl} -e %{script}


# Standard JPackage naming and versioning defines.
%global origin          openjdk
# note, following three variables are sedded from update_sources if used correctly. Hardcode them rather there.
%global project         aarch64-port
%global repo            jdk8u
%global revision        aarch64-jdk8u151-b12
# eg # jdk8u60-b27 -> jdk8u60 or # aarch64-jdk8u60-b27 -> aarch64-jdk8u60  (dont forget spec escape % by %%)
%global whole_update    %(VERSION=%{revision}; echo ${VERSION%%-*})
# eg  jdk8u60 -> 60 or aarch64-jdk8u60 -> 60
%global updatever       %(VERSION=%{whole_update}; echo ${VERSION##*u})
# eg jdk8u60-b27 -> b27
%global buildver        %(VERSION=%{revision}; echo ${VERSION##*-})
# priority must be 7 digits in total. The expression is workarounding tip
%global priority        %(TIP=1800%{updatever};  echo ${TIP/tip/999})

%global javaver         1.8.0

# parametrized macros are order-sensitive
%global fullversion     %{name}-%{version}-%{release}
#images stub
%global j2sdkimage       j2sdk-image
# output dir stub
%define buildoutputdir() %{expand:openjdk/build/jdk8.build%{?1}}
#we can copy the javadoc to not arched dir, or made it not noarch
%define uniquejavadocdir()    %{expand:%{fullversion}%{?1}}
#main id and dir of this jdk
%define uniquesuffix()        %{expand:%{fullversion}.%{_arch}%{?1}}

# Standard JPackage directories and symbolic links.
%define sdkdir()        %{expand:%{uniquesuffix -- %{?1}}}
%define jrelnk()        %{expand:jre-%{javaver}-%{origin}-%{version}-%{release}.%{_arch}%{?1}}

%define jredir()        %{expand:%{sdkdir -- %{?1}}/jre}
%define sdkbindir()     %{expand:%{_jvmdir}/%{sdkdir -- %{?1}}/bin}
%define jrebindir()     %{expand:%{_jvmdir}/%{jredir -- %{?1}}/bin}

%global rpm_state_dir %{_localstatedir}/lib/rpm-state/

%if %{with_systemtap}
# Where to install systemtap tapset (links)
# We would like these to be in a package specific subdir,
# but currently systemtap doesn't support that, so we have to
# use the root tapset dir for now. To distinquish between 64
# and 32 bit architectures we place the tapsets under the arch
# specific dir (note that systemtap will only pickup the tapset
# for the primary arch for now). Systemtap uses the machine name
# aka build_cpu as architecture specific directory name.
%global tapsetroot /usr/share/systemtap
%global tapsetdir %{tapsetroot}/tapset/%{stapinstall}
%endif

# not-duplicated scriplets for normal/debug packages
%global update_desktop_icons /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :


%define post_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
exit 0
}


%define post_headless() %{expand:
%ifarch %{jit_arches}
# MetaspaceShared::generate_vtable_methods not implemented for PPC JIT
%ifnarch %{power64}
#see https://bugzilla.redhat.com/show_bug.cgi?id=513605
%{jrebindir -- %{?1}}/java -Xshare:dump >/dev/null 2>/dev/null
%endif
%endif

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
alternatives \\
  --install %{_bindir}/java java %{jrebindir -- %{?1}}/java $PRIORITY  --family %{name}.%{_arch} \\
  --slave %{_jvmdir}/jre jre %{_jvmdir}/%{jredir -- %{?1}} \\
  --slave %{_bindir}/jjs jjs %{jrebindir -- %{?1}}/jjs \\
  --slave %{_bindir}/keytool keytool %{jrebindir -- %{?1}}/keytool \\
  --slave %{_bindir}/orbd orbd %{jrebindir -- %{?1}}/orbd \\
  --slave %{_bindir}/pack200 pack200 %{jrebindir -- %{?1}}/pack200 \\
  --slave %{_bindir}/rmid rmid %{jrebindir -- %{?1}}/rmid \\
  --slave %{_bindir}/rmiregistry rmiregistry %{jrebindir -- %{?1}}/rmiregistry \\
  --slave %{_bindir}/servertool servertool %{jrebindir -- %{?1}}/servertool \\
  --slave %{_bindir}/tnameserv tnameserv %{jrebindir -- %{?1}}/tnameserv \\
  --slave %{_bindir}/policytool policytool %{jrebindir -- %{?1}}/policytool \\
  --slave %{_bindir}/unpack200 unpack200 %{jrebindir -- %{?1}}/unpack200 \\
  --slave %{_mandir}/man1/java.1$ext java.1$ext \\
  %{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jjs.1$ext jjs.1$ext \\
  %{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/keytool.1$ext keytool.1$ext \\
  %{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/orbd.1$ext orbd.1$ext \\
  %{_mandir}/man1/orbd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/pack200.1$ext pack200.1$ext \\
  %{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmid.1$ext rmid.1$ext \\
  %{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmiregistry.1$ext rmiregistry.1$ext \\
  %{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/servertool.1$ext servertool.1$ext \\
  %{_mandir}/man1/servertool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/tnameserv.1$ext tnameserv.1$ext \\
  %{_mandir}/man1/tnameserv-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/policytool.1$ext policytool.1$ext \\
  %{_mandir}/man1/policytool-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/unpack200.1$ext unpack200.1$ext \\
  %{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1$ext

for X in %{origin} %{javaver} ; do
  alternatives --install %{_jvmdir}/jre-"$X" jre_"$X" %{_jvmdir}/%{jredir -- %{?1}} $PRIORITY --family %{name}.%{_arch}
done

update-alternatives --install %{_jvmdir}/jre-%{javaver}-%{origin} jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk -- %{?1}} $PRIORITY  --family %{name}.%{_arch}


update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

# see pretrans where this file is declared
# also see that pretrans is only for nondebug
if [ ! "%{?1}" == %{debug_suffix} ]; then
  if [ -f %{_libexecdir}/copy_jdk_configs_fixFiles.sh ] ; then
    sh  %{_libexecdir}/copy_jdk_configs_fixFiles.sh %{rpm_state_dir}/%{name}.%{_arch}  %{_jvmdir}/%{sdkdir -- %{?1}}
  fi
fi

exit 0
}

%define postun_script() %{expand:
update-desktop-database %{_datadir}/applications &> /dev/null || :
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}


%define postun_headless() %{expand:
  alternatives --remove java %{jrebindir -- %{?1}}/java
  alternatives --remove jre_%{origin} %{_jvmdir}/%{jredir -- %{?1}}
  alternatives --remove jre_%{javaver} %{_jvmdir}/%{jredir -- %{?1}}
  alternatives --remove jre_%{javaver}_%{origin} %{_jvmdir}/%{jrelnk -- %{?1}}
}

%define posttrans_script() %{expand:
%{update_desktop_icons}
}

%define post_devel() %{expand:

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

ext=.gz
alternatives \\
  --install %{_bindir}/javac javac %{sdkbindir -- %{?1}}/javac $PRIORITY  --family %{name}.%{_arch} \\
  --slave %{_jvmdir}/java java_sdk %{_jvmdir}/%{sdkdir -- %{?1}} \\
  --slave %{_bindir}/appletviewer appletviewer %{sdkbindir -- %{?1}}/appletviewer \\
  --slave %{_bindir}/extcheck extcheck %{sdkbindir -- %{?1}}/extcheck \\
  --slave %{_bindir}/idlj idlj %{sdkbindir -- %{?1}}/idlj \\
  --slave %{_bindir}/jar jar %{sdkbindir -- %{?1}}/jar \\
  --slave %{_bindir}/jarsigner jarsigner %{sdkbindir -- %{?1}}/jarsigner \\
  --slave %{_bindir}/javadoc javadoc %{sdkbindir -- %{?1}}/javadoc \\
  --slave %{_bindir}/javah javah %{sdkbindir -- %{?1}}/javah \\
  --slave %{_bindir}/javap javap %{sdkbindir -- %{?1}}/javap \\
  --slave %{_bindir}/jcmd jcmd %{sdkbindir -- %{?1}}/jcmd \\
  --slave %{_bindir}/jconsole jconsole %{sdkbindir -- %{?1}}/jconsole \\
  --slave %{_bindir}/jdb jdb %{sdkbindir -- %{?1}}/jdb \\
  --slave %{_bindir}/jdeps jdeps %{sdkbindir -- %{?1}}/jdeps \\
  --slave %{_bindir}/jhat jhat %{sdkbindir -- %{?1}}/jhat \\
  --slave %{_bindir}/jinfo jinfo %{sdkbindir -- %{?1}}/jinfo \\
  --slave %{_bindir}/jmap jmap %{sdkbindir -- %{?1}}/jmap \\
  --slave %{_bindir}/jps jps %{sdkbindir -- %{?1}}/jps \\
  --slave %{_bindir}/jrunscript jrunscript %{sdkbindir -- %{?1}}/jrunscript \\
  --slave %{_bindir}/jsadebugd jsadebugd %{sdkbindir -- %{?1}}/jsadebugd \\
  --slave %{_bindir}/jstack jstack %{sdkbindir -- %{?1}}/jstack \\
  --slave %{_bindir}/jstat jstat %{sdkbindir -- %{?1}}/jstat \\
  --slave %{_bindir}/jstatd jstatd %{sdkbindir -- %{?1}}/jstatd \\
  --slave %{_bindir}/native2ascii native2ascii %{sdkbindir -- %{?1}}/native2ascii \\
  --slave %{_bindir}/rmic rmic %{sdkbindir -- %{?1}}/rmic \\
  --slave %{_bindir}/schemagen schemagen %{sdkbindir -- %{?1}}/schemagen \\
  --slave %{_bindir}/serialver serialver %{sdkbindir -- %{?1}}/serialver \\
  --slave %{_bindir}/wsgen wsgen %{sdkbindir -- %{?1}}/wsgen \\
  --slave %{_bindir}/wsimport wsimport %{sdkbindir -- %{?1}}/wsimport \\
  --slave %{_bindir}/xjc xjc %{sdkbindir -- %{?1}}/xjc \\
  --slave %{_mandir}/man1/appletviewer.1$ext appletviewer.1$ext \\
  %{_mandir}/man1/appletviewer-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/extcheck.1$ext extcheck.1$ext \\
  %{_mandir}/man1/extcheck-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/idlj.1$ext idlj.1$ext \\
  %{_mandir}/man1/idlj-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jar.1$ext jar.1$ext \\
  %{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jarsigner.1$ext jarsigner.1$ext \\
  %{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javac.1$ext javac.1$ext \\
  %{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javadoc.1$ext javadoc.1$ext \\
  %{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javah.1$ext javah.1$ext \\
  %{_mandir}/man1/javah-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/javap.1$ext javap.1$ext \\
  %{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jcmd.1$ext jcmd.1$ext \\
  %{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jconsole.1$ext jconsole.1$ext \\
  %{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdb.1$ext jdb.1$ext \\
  %{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jdeps.1$ext jdeps.1$ext \\
  %{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jhat.1$ext jhat.1$ext \\
  %{_mandir}/man1/jhat-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jinfo.1$ext jinfo.1$ext \\
  %{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jmap.1$ext jmap.1$ext \\
  %{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jps.1$ext jps.1$ext \\
  %{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jrunscript.1$ext jrunscript.1$ext \\
  %{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jsadebugd.1$ext jsadebugd.1$ext \\
  %{_mandir}/man1/jsadebugd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstack.1$ext jstack.1$ext \\
  %{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstat.1$ext jstat.1$ext \\
  %{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/jstatd.1$ext jstatd.1$ext \\
  %{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/native2ascii.1$ext native2ascii.1$ext \\
  %{_mandir}/man1/native2ascii-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/rmic.1$ext rmic.1$ext \\
  %{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/schemagen.1$ext schemagen.1$ext \\
  %{_mandir}/man1/schemagen-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/serialver.1$ext serialver.1$ext \\
  %{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/wsgen.1$ext wsgen.1$ext \\
  %{_mandir}/man1/wsgen-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/wsimport.1$ext wsimport.1$ext \\
  %{_mandir}/man1/wsimport-%{uniquesuffix -- %{?1}}.1$ext \\
  --slave %{_mandir}/man1/xjc.1$ext xjc.1$ext \\
  %{_mandir}/man1/xjc-%{uniquesuffix -- %{?1}}.1$ext

for X in %{origin} %{javaver} ; do
  alternatives \\
    --install %{_jvmdir}/java-"$X" java_sdk_"$X" %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{name}.%{_arch}
done

update-alternatives --install %{_jvmdir}/java-%{javaver}-%{origin} java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}} $PRIORITY  --family %{name}.%{_arch}

update-desktop-database %{_datadir}/applications &> /dev/null || :
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :

exit 0
}

%define postun_devel() %{expand:
  alternatives --remove javac %{sdkbindir -- %{?1}}/javac
  alternatives --remove java_sdk_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}}
  alternatives --remove java_sdk_%{javaver} %{_jvmdir}/%{sdkdir -- %{?1}}
  alternatives --remove java_sdk_%{javaver}_%{origin} %{_jvmdir}/%{sdkdir -- %{?1}}

update-desktop-database %{_datadir}/applications &> /dev/null || :

if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    %{update_desktop_icons}
fi
exit 0
}

%define posttrans_devel() %{expand:
%{update_desktop_icons}
}

%define post_javadoc() %{expand:

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

alternatives \\
  --install %{_javadocdir}/java javadocdir %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api \\
  $PRIORITY  --family %{name}
exit 0
}

%define postun_javadoc() %{expand:
  alternatives --remove javadocdir %{_javadocdir}/%{uniquejavadocdir -- %{?1}}/api
exit 0
}

%define post_javadoc_zip() %{expand:

PRIORITY=%{priority}
if [ "%{?1}" == %{debug_suffix} ]; then
  let PRIORITY=PRIORITY-1
fi

alternatives \\
  --install %{_javadocdir}/java-zip javadoczip %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip \\
  $PRIORITY  --family %{name}
exit 0
}

%define postun_javadoc_zip() %{expand:
  alternatives --remove javadoczip %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip
exit 0
}

%define files_jre() %{expand:
%{_datadir}/icons/hicolor/*x*/apps/java-%{javaver}.png
%{_datadir}/applications/*policytool%{?1}.desktop
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libjsoundalsa.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libsplashscreen.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libawt_xawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/lib/%{archinstall}/libjawt.so
%{_jvmdir}/%{sdkdir -- %{?1}}/jre/bin/policytool
}


%define files_jre_headless() %{expand:
%defattr(-,root,root,-)
%dir %{_sysconfdir}/.java/.systemPrefs
%dir %{_sysconfdir}/.java
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/jre/ASSEMBLY_EXCEPTION
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/jre/LICENSE
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/jre/THIRD_PARTY_README
%dir %{_jvmdir}/%{sdkdir -- %{?1}}
%{_jvmdir}/%{jrelnk -- %{?1}}
%{_jvmprivdir}/*
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/security
%{_jvmdir}/%{jredir -- %{?1}}/lib/security/cacerts
%dir %{_jvmdir}/%{jredir -- %{?1}}
%dir %{_jvmdir}/%{jredir -- %{?1}}/bin
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib
%{_jvmdir}/%{jredir -- %{?1}}/bin/java
%{_jvmdir}/%{jredir -- %{?1}}/bin/jjs
%{_jvmdir}/%{jredir -- %{?1}}/bin/keytool
%{_jvmdir}/%{jredir -- %{?1}}/bin/orbd
%{_jvmdir}/%{jredir -- %{?1}}/bin/pack200
%{_jvmdir}/%{jredir -- %{?1}}/bin/rmid
%{_jvmdir}/%{jredir -- %{?1}}/bin/rmiregistry
%{_jvmdir}/%{jredir -- %{?1}}/bin/servertool
%{_jvmdir}/%{jredir -- %{?1}}/bin/tnameserv
%{_jvmdir}/%{jredir -- %{?1}}/bin/unpack200
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/unlimited/US_export_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/unlimited/local_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/limited/US_export_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/policy/limited/local_policy.jar
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/java.policy
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/java.security
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/blacklisted.certs
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/logging.properties
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/calendars.properties
%{_mandir}/man1/java-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jjs-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/keytool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/orbd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/pack200-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmid-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmiregistry-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/servertool-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/tnameserv-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/unpack200-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/policytool-%{uniquesuffix -- %{?1}}.1*
%config(noreplace) %{_jvmdir}/%{jredir -- %{?1}}/lib/security/nss.cfg
%ifarch %{jit_arches}
%ifnarch %{power64}
%attr(664, root, root) %ghost %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/server/classes.jsa
%attr(664, root, root) %ghost %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/client/classes.jsa
%endif
%endif
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/server/
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/client/
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/jli
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/jli/libjli.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/jvm.cfg
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libattach.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libawt.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libawt_headless.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libdt_socket.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libfontmanager.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libhprof.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libinstrument.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libj2gss.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libj2pcsc.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libj2pkcs11.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjaas_unix.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjava.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjava_crw_demo.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjavajpeg.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjdwp.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjsdt.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjsig.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libjsound.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/liblcms.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libmanagement.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libmlib_image.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libnet.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libnio.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libnpt.so
%ifarch x86_64  %{ix86} %{aarch64}
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsaproc.so
%endif
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsctp.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libsunec.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libunpack.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libverify.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libzip.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/charsets.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/classlist
%{_jvmdir}/%{jredir -- %{?1}}/lib/content-types.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/currency.data
%{_jvmdir}/%{jredir -- %{?1}}/lib/flavormap.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/hijrah-config-umalqura.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/images/cursors/*
%{_jvmdir}/%{jredir -- %{?1}}/lib/jce.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/jexec
%{_jvmdir}/%{jredir -- %{?1}}/lib/jsse.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/jvm.hprof.txt
%{_jvmdir}/%{jredir -- %{?1}}/lib/meta-index
%{_jvmdir}/%{jredir -- %{?1}}/lib/net.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/psfont.properties.ja
%{_jvmdir}/%{jredir -- %{?1}}/lib/psfontj2d.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/resources.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/rt.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/sound.properties
%{_jvmdir}/%{jredir -- %{?1}}/lib/tzdb.dat
%{_jvmdir}/%{jredir -- %{?1}}/lib/management-agent.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/management/*
%{_jvmdir}/%{jredir -- %{?1}}/lib/cmm/*
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/*
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/images
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/images/cursors
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/management
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/cmm
%dir %{_jvmdir}/%{jredir -- %{?1}}/lib/ext
}

%define files_devel() %{expand:
%defattr(-,root,root,-)
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/ASSEMBLY_EXCEPTION
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/LICENSE
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/THIRD_PARTY_README
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/bin
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/include
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/lib
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/appletviewer
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/extcheck
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/idlj
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jar
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jarsigner
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/java
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javac
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javadoc
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javah
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/javap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/java-rmi.cgi
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jcmd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jconsole
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdb
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jdeps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jhat
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jinfo
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jjs
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jmap
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jps
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jrunscript
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jsadebugd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstack
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstat
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/jstatd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/keytool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/native2ascii
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/orbd
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/pack200
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/policytool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmic
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmid
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/rmiregistry
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/schemagen
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/serialver
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/servertool
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/tnameserv
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/unpack200
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/wsgen
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/wsimport
%{_jvmdir}/%{sdkdir -- %{?1}}/bin/xjc
%{_jvmdir}/%{sdkdir -- %{?1}}/include/*
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/%{archinstall}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/ct.sym
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/ir.idl
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jconsole.jar
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/orb.idl
%ifarch x86_64  %{ix86}
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/sa-jdi.jar
%endif
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/dt.jar
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/jexec
%{_jvmdir}/%{sdkdir -- %{?1}}/lib/tools.jar
%{_datadir}/applications/*jconsole%{?1}.desktop
%{_mandir}/man1/appletviewer-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/extcheck-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/idlj-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jar-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jarsigner-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javac-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javadoc-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javah-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/javap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jconsole-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jcmd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdb-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jdeps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jhat-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jinfo-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jmap-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jps-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jrunscript-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jsadebugd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstack-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstat-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/jstatd-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/native2ascii-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/rmic-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/schemagen-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/serialver-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/wsgen-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/wsimport-%{uniquesuffix -- %{?1}}.1*
%{_mandir}/man1/xjc-%{uniquesuffix -- %{?1}}.1*
%if %{with_systemtap}
%dir %{tapsetroot}
%dir %{tapsetdir}
%{tapsetdir}/*%{version}-%{release}.%{_arch}%{?1}.stp
%dir %{_jvmdir}/%{sdkdir -- %{?1}}/tapset
%{_jvmdir}/%{sdkdir -- %{?1}}/tapset/*.stp
%endif
}

%define files_demo() %{expand:
%defattr(-,root,root,-)
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/jre/LICENSE
}

%define files_src() %{expand:
%defattr(-,root,root,-)
%doc README.src
%{_jvmdir}/%{sdkdir -- %{?1}}/src.zip
}

%define files_javadoc() %{expand:
%defattr(-,root,root,-)
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/jre/LICENSE
}

%define files_javadoc_zip() %{expand:
%defattr(-,root,root,-)
%doc %{_javadocdir}/%{uniquejavadocdir -- %{?1}}.zip
%license %{buildoutputdir -- %{?1}}/images/%{j2sdkimage}/jre/LICENSE
}

%define files_accessibility() %{expand:
%{_jvmdir}/%{jredir -- %{?1}}/lib/%{archinstall}/libatk-wrapper.so
%{_jvmdir}/%{jredir -- %{?1}}/lib/ext/java-atk-wrapper.jar
%{_jvmdir}/%{jredir -- %{?1}}/lib/accessibility.properties
}

# not-duplicated requires/provides/obsolate for normal/debug packages
%define java_rpo() %{expand:
Requires: fontconfig%{?_isa}
Requires: xorg-x11-fonts-Type1

# Requires rest of java
Requires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}


# Standard JPackage base provides.
Provides: jre-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}%{?1} = %{epoch}:%{version}-%{release}
Provides: jre = %{javaver}%{?1}
Provides: java-%{origin}%{?1} = %{epoch}:%{version}-%{release}
Provides: java%{?1} = %{epoch}:%{javaver}
# Standard JPackage extensions provides.
Provides: java-fonts%{?1} = %{epoch}:%{version}

Obsoletes: java-1.7.0-openjdk%{?1}
Obsoletes: java-1.5.0-gcj%{?1}
Obsoletes: sinjdoc
}

%define java_headless_rpo() %{expand:
# Require /etc/pki/java/cacerts.
Requires: ca-certificates
# Require javapackages-tools for ownership of /usr/lib/jvm/
Requires: javapackages-tools
# Require zoneinfo data provided by tzdata-java subpackage.
Requires: tzdata-java >= 2015d
# libsctp.so.1 is being `dlopen`ed on demand
Requires: lksctp-tools%{?_isa}
# there is a need to depend on the exact version of NSS
Requires: nss%{?_isa} %{NSS_BUILDTIME_VERSION}
Requires: nss-softokn%{?_isa} %{NSSSOFTOKN_BUILDTIME_VERSION}
# tool to copy jdk's configs - should be Recommends only, but then only dnf/yum eforce it, not rpm transaction and so no configs are persisted when pure rpm -u is run. I t may be consiedered as regression
Requires:	copy-jdk-configs >= 3.3
OrderWithRequires: copy-jdk-configs
# Post requires alternatives to install tool alternatives.
Requires(post):   %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall tool alternatives.
Requires(postun): %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage base provides.
Provides: jre-%{javaver}-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-%{javaver}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: jre-headless%{?1} = %{epoch}:%{javaver}
Provides: java-%{origin}-headless%{?1} = %{epoch}:%{version}-%{release}
Provides: java-headless%{?1} = %{epoch}:%{javaver}
# Standard JPackage extensions provides.
Provides: jndi%{?1} = %{epoch}:%{version}
Provides: jndi-ldap%{?1} = %{epoch}:%{version}
Provides: jndi-cos%{?1} = %{epoch}:%{version}
Provides: jndi-rmi%{?1} = %{epoch}:%{version}
Provides: jndi-dns%{?1} = %{epoch}:%{version}
Provides: jaas%{?1} = %{epoch}:%{version}
Provides: jsse%{?1} = %{epoch}:%{version}
Provides: jce%{?1} = %{epoch}:%{version}
Provides: jdbc-stdext%{?1} = 4.1
Provides: java-sasl%{?1} = %{epoch}:%{version}

#https://bugzilla.redhat.com/show_bug.cgi?id=1312019
Provides: /usr/bin/jjs

Obsoletes: java-1.7.0-openjdk-headless%{?1}
}

%define java_devel_rpo() %{expand:
# Require base package.
Requires:         %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# Post requires alternatives to install tool alternatives.
Requires(post):   %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall tool alternatives.
Requires(postun): %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage devel provides.
Provides: java-sdk-%{javaver}-%{origin}%{?1} = %{epoch}:%{version}
Provides: java-sdk-%{javaver}%{?1} = %{epoch}:%{version}
Provides: java-sdk-%{origin}%{?1} = %{epoch}:%{version}
Provides: java-sdk%{?1} = %{epoch}:%{javaver}
Provides: java-%{javaver}-devel%{?1} = %{epoch}:%{version}
Provides: java-devel-%{origin}%{?1} = %{epoch}:%{version}
Provides: java-devel%{?1} = %{epoch}:%{javaver}

Obsoletes: java-1.7.0-openjdk-devel%{?1}
Obsoletes: java-1.5.0-gcj-devel%{?1}
}


%define java_demo_rpo() %{expand:
Requires: %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

Provides: java-%{javaver}-%{origin}-demo = %{epoch}:%{version}-%{release}

Obsoletes: java-1.7.0-openjdk-demo%{?1}
}

%define java_javadoc_rpo() %{expand:
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
# Post requires alternatives to install javadoc alternative.
Requires(post):   %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(post):   chkconfig >= 1.7
# Postun requires alternatives to uninstall javadoc alternative.
Requires(postun): %{_sbindir}/alternatives
# in version 1.7 and higher for --family switch
Requires(postun):   chkconfig >= 1.7

# Standard JPackage javadoc provides.
Provides: java-javadoc%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-javadoc%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-javadoc = %{epoch}:%{version}-%{release}

Obsoletes: java-1.7.0-openjdk-javadoc%{?1}

}

%define java_src_rpo() %{expand:
Requires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

# Standard JPackage javadoc provides.
Provides: java-src%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-src%{?1} = %{epoch}:%{version}-%{release}
Provides: java-%{javaver}-%{origin}-src = %{epoch}:%{version}-%{release}
Obsoletes: java-1.7.0-openjdk-src%{?1}
}

%define java_accessibility_rpo() %{expand:
Requires: java-atk-wrapper%{?_isa}
Requires: %{name}%{?1}%{?_isa} = %{epoch}:%{version}-%{release}
OrderWithRequires: %{name}-headless%{?1}%{?_isa} = %{epoch}:%{version}-%{release}

Provides: java-%{javaver}-%{origin}-accessibility = %{epoch}:%{version}-%{release}

Obsoletes: java-1.7.0-openjdk-accessibility%{?1}
}

# Prevent brp-java-repack-jars from being run.
%global __jar_repack 0

Name:    java-%{javaver}-%{origin}
Version: %{javaver}.%{updatever}
Release: 2.%{buildver}%{?dist}
# java-1.5.0-ibm from jpackage.org set Epoch to 1 for unknown reasons,
# and this change was brought into RHEL-4.  java-1.5.0-ibm packages
# also included the epoch in their virtual provides.  This created a
# situation where in-the-wild java-1.5.0-ibm packages provided "java =
# 1:1.5.0".  In RPM terms, "1.6.0 < 1:1.5.0" since 1.6.0 is
# interpreted as 0:1.6.0.  So the "java >= 1.6.0" requirement would be
# satisfied by the 1:1.5.0 packages.  Thus we need to set the epoch in
# JDK package >= 1.6.0 to 1, and packages referring to JDK virtual
# provides >= 1.6.0 must specify the epoch, "java >= 1:1.6.0".

Epoch:   1
Summary: OpenJDK Runtime Environment
Group:   Development/Languages

License:  ASL 1.1 and ASL 2.0 and GPL+ and GPLv2 and GPLv2 with exceptions and LGPL+ and LGPLv2 and MPLv1.0 and MPLv1.1 and Public Domain and W3C
URL:      http://openjdk.java.net/

# aarch64-port now contains integration forest of both aarch64 and normal jdk
# Source from upstream OpenJDK8 project. To regenerate, use
# VERSION=%%{revision} FILE_NAME_ROOT=%%{project}-%%{repo}-${VERSION}
# REPO_ROOT=<path to checked-out repository> generate_source_tarball.sh
# where the source is obtained from http://hg.openjdk.java.net/%%{project}/%%{repo}
Source0: %{project}-%{repo}-%{revision}.tar.xz

# Shenandoah HotSpot
Source1: aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u151-b12.tar.xz

# Custom README for -src subpackage
Source2:  README.src

# Use 'generate_tarballs.sh' to generate the following tarballs
# They are based on code contained in the IcedTea7 project.

# Systemtap tapsets. Zipped up to keep it small.
Source8: systemtap-tapset-3.6.0pre02.tar.xz

# Desktop files. Adapated from IcedTea.
Source9: jconsole.desktop.in
Source10: policytool.desktop.in

# nss configuration file
Source11: nss.cfg.in

# Removed libraries that we link instead
Source12: %{name}-remove-intree-libraries.sh

# Ensure we aren't using the limited crypto policy
Source13: TestCryptoLevel.java

# Ensure ECDSA is working
Source14: TestECDSA.java

Source20: repackReproduciblePolycies.sh

# New versions of config files with aarch64 support. This is not upstream yet.
Source100: config.guess
Source101: config.sub

# RPM/distribution specific patches

# Accessibility patches
# Ignore AWTError when assistive technologies are loaded 
Patch1:   %{name}-accessible-toolkit.patch
# Restrict access to java-atk-wrapper classes
Patch3: java-atk-wrapper-security.patch

# Upstreamable patches
# PR2737: Allow multiple initialization of PKCS11 libraries
Patch5: multiple-pkcs11-library-init.patch
# PR2095, RH1163501: 2048-bit DH upper bound too small for Fedora infrastructure (sync with IcedTea 2.x)
Patch504: rh1163501.patch
# S4890063, PR2304, RH1214835: HPROF: default text truncated when using doe=n option
Patch511: rh1214835.patch
# Turn off strict overflow on IndicRearrangementProcessor{,2}.cpp following 8140543: Arrange font actions
Patch512: no_strict_overflow.patch
# Support for building the SunEC provider with the system NSS installation
# PR1983: Support using the system installation of NSS with the SunEC provider
# PR2127: SunEC provider crashes when built using system NSS
# PR2815: Race condition in SunEC provider with system NSS
# PR2899: Don't use WithSeed versions of NSS functions as they don't fully process the seed
# PR2934: SunEC provider throwing KeyException with current NSS
# PR3479, RH1486025: ECC and NSS JVM crash
Patch513: pr1983-jdk.patch
Patch514: pr1983-root.patch
Patch515: pr2127.patch
Patch516: pr2815.patch
Patch517: pr2899.patch
Patch518: pr2934.patch
Patch519: pr3479-rh1486025.patch
# S8150954, RH1176206, PR2866: Taking screenshots on x11 composite desktop produces wrong result
# In progress: http://mail.openjdk.java.net/pipermail/awt-dev/2016-March/010742.html
Patch508: rh1176206-jdk.patch
Patch509: rh1176206-root.patch
# RH1337583, PR2974: PKCS#10 certificate requests now use CRLF line endings rather than system line endings
Patch523: pr2974-rh1337583.patch
# PR3083, RH1346460: Regression in SSL debug output without an ECC provider
Patch528: pr3083-rh1346460.patch
# Patches 204 and 205 stop the build adding .gnu_debuglink sections to unstripped files
Patch204: hotspot-remove-debuglink.patch
Patch205: dont-add-unnecessary-debug-links.patch
# Enable debug information for assembly code files
Patch206: hotspot-assembler-debuginfo.patch
# 8188030, PR3459, RH1484079: AWT java apps fail to start when some minimal fonts are present
Patch560: 8188030-pr3459-rh1484079.patch

# Arch-specific upstreamable patches
# PR2415: JVM -Xmx requirement is too high on s390
Patch100: %{name}-s390-java-opts.patch
# Type fixing for s390
Patch102: %{name}-size_t.patch
# Use "%z" for size_t on s390 as size_t != intptr_t
Patch103: s390-size_t_format_flags.patch

# Patches which need backporting to 8u
# S8073139, RH1191652; fix name of ppc64le architecture
Patch601: %{name}-rh1191652-root.patch
Patch602: %{name}-rh1191652-jdk.patch
Patch603: %{name}-rh1191652-hotspot-aarch64.patch
# Include all sources in src.zip
Patch7: include-all-srcs.patch
# 8035341: Allow using a system installed libpng
Patch202: system-libpng.patch
# 8042159: Allow using a system-installed lcms2
Patch203: system-lcms.patch
# PR2462: Backport "8074839: Resolve disabled warnings for libunpack and the unpack200 binary"
# This fixes printf warnings that lead to build failure with -Werror=format-security from optflags
Patch502: pr2462.patch
# S8148351, PR2842: Only display resolved symlink for compiler, do not change path
Patch506: pr2842-01.patch
Patch507: pr2842-02.patch
# S8154313: Generated javadoc scattered all over the place
Patch400: 8154313.patch
# S6260348, PR3066: GTK+ L&F JTextComponent not respecting desktop caret blink rate
Patch526: 6260348-pr3066.patch
# 8061305, PR3335, RH1423421: Javadoc crashes when method name ends with "Property"
Patch538: 8061305-pr3335-rh1423421.patch

# Patches upstream and appearing in 8u151
# 8075484, PR3473, RH1490713: SocketInputStream.socketRead0 can hang even with soTimeout set
Patch561: 8075484-pr3473-rh1490713.patch

# Patches upstream and appearing in 8u152
# 8153711, PR3313, RH1284948: [REDO] JDWP: Memory Leak: GlobalRefs never deleted when processing invokeMethod command
Patch535: 8153711-pr3313-rh1284948.patch
# 8162384, PR3122, RH1358661: Performance regression: bimorphic inlining may be bypassed by type speculation
Patch532: 8162384-pr3122-rh1358661.patch
# 8173941, PR3326: SA does not work if executable is DSO
Patch547: 8173941-pr3326.patch
# 8175813, PR3394, RH1448880: PPC64: "mbind: Invalid argument" when -XX:+UseNUMA is used
Patch550: 8175813-pr3394-rh1448880.patch
# 8175887, PR3415: C1 value numbering handling of Unsafe.get*Volatile is incorrect
Patch554: 8175887-pr3415.patch

# Patches upstream and appearing in 8u161
# 8164293, PR3412, RH1459641: HotSpot leaking memory in long-running requests
Patch555: 8164293-pr3412-rh1459641.patch
 
# Patches upstream and appearing in 8u162
# 8181055, PR3394, RH1448880: PPC64: "mbind: Invalid argument" still seen after 8175813
Patch551: 8181055-pr3394-rh1448880.patch
# 8181419, PR3413, RH1463144: Race in jdwp invoker handling may lead to crashes or invalid results
Patch553: 8181419-pr3413-rh1463144.patch
# 8145913, PR3466, RH1498309: PPC64: add Montgomery multiply intrinsic
Patch556: 8145913-pr3466-rh1498309.patch
# 8168318, PR3466, RH1498320: PPC64: Use cmpldi instead of li/cmpld
Patch557: 8168318-pr3466-rh1498320.patch
# 8170328, PR3466, RH1498321: PPC64: Use andis instead of lis/and
Patch558: 8170328-pr3466-rh1498321.patch
# 8181810, PR3466, RH1498319: PPC64: Leverage extrdi for bitfield extract
Patch559: 8181810-pr3466-rh1498319.patch

# Patches ineligible for 8u
# 8043805: Allow using a system-installed libjpeg
Patch201: system-libjpeg.patch
# custom securities
Patch207: PR3183.patch
# ustreamed aarch64 fixes
Patch208: aarch64BuildFailure.patch
Patch209: 8035496-hotspot.patch
Patch210: suse_linuxfilestore.patch

# Local fixes
# PR1834, RH1022017: Reduce curves reported by SSL to those in NSS
Patch525: pr1834-rh1022017.patch
# Turn on AssumeMP by default on RHEL systems
Patch534: always_assumemp.patch
# PR2888: OpenJDK should check for system cacerts database (e.g. /etc/pki/java/cacerts)
Patch539: pr2888.patch

# Non-OpenJDK fixes
Patch1000: enableCommentedOutSystemNss.patch

BuildRequires: autoconf
BuildRequires: automake
BuildRequires: alsa-lib-devel
BuildRequires: binutils
BuildRequires: cups-devel
BuildRequires: desktop-file-utils
BuildRequires: elfutils
BuildRequires: fontconfig
BuildRequires: freetype-devel
BuildRequires: giflib-devel
BuildRequires: gcc-c++
BuildRequires: gdb
BuildRequires: gtk2-devel
BuildRequires: lcms2-devel
BuildRequires: libjpeg-devel
BuildRequires: libpng-devel
BuildRequires: libxslt
BuildRequires: libX11-devel
BuildRequires: libXi-devel
BuildRequires: libXinerama-devel
BuildRequires: libXt-devel
BuildRequires: libXtst-devel
# Requirements for setting up the nss.cfg
BuildRequires: nss-devel
BuildRequires: pkgconfig
BuildRequires: xorg-x11-proto-devel
BuildRequires: zip
# Use OpenJDK 7 where available (on RHEL) to avoid
# having to use the rhel-7.x-java-unsafe-candidate hack
%if ! 0%{?fedora} && 0%{?rhel} <= 7
BuildRequires: java-1.7.0-openjdk-devel
%else
BuildRequires: java-1.8.0-openjdk-devel
%endif
# Zero-assembler build requirement.
%ifnarch %{jit_arches}
BuildRequires: libffi-devel
%endif
BuildRequires: tzdata-java >= 2015d
# Earlier versions have a bug in tree vectorization on PPC
BuildRequires: gcc >= 4.8.3-8
# Build requirements for SunEC system NSS support
BuildRequires: nss-softokn-freebl-devel >= 3.16.1

%if %{with_systemtap}
BuildRequires: systemtap-sdt-devel
%endif

# this is built always, also during debug-only build
# when it is built in debug-only, then this package is just placeholder
%{java_rpo %{nil}}

%description
The OpenJDK runtime environment.

%if %{include_debug_build}
%package debug
Summary: OpenJDK Runtime Environment %{debug_on}
Group:   Development/Languages

%{java_rpo -- %{debug_suffix_unquoted}}
%description debug
The OpenJDK runtime environment.
%{debug_warning}
%endif

%if %{include_normal_build}
%package headless
Summary: OpenJDK Runtime Environment
Group:   Development/Languages

%{java_headless_rpo %{nil}}

%description headless
The OpenJDK runtime environment without audio and video support.
%endif

%if %{include_debug_build}
%package headless-debug
Summary: OpenJDK Runtime Environment %{debug_on}
Group:   Development/Languages

%{java_headless_rpo -- %{debug_suffix_unquoted}}

%description headless-debug
The OpenJDK runtime environment without audio and video support.
%{debug_warning}
%endif

%if %{include_normal_build}
%package devel
Summary: OpenJDK Development Environment
Group:   Development/Tools

%{java_devel_rpo %{nil}}

%description devel
The OpenJDK development tools.
%endif

%if %{include_debug_build}
%package devel-debug
Summary: OpenJDK Development Environment %{debug_on}
Group:   Development/Tools

%{java_devel_rpo -- %{debug_suffix_unquoted}}

%description devel-debug
The OpenJDK development tools.
%{debug_warning}
%endif

%if %{include_normal_build}
%package demo
Summary: OpenJDK Demos
Group:   Development/Languages

%{java_demo_rpo %{nil}}

%description demo
The OpenJDK demos.
%endif

%if %{include_debug_build}
%package demo-debug
Summary: OpenJDK Demos %{debug_on}
Group:   Development/Languages

%{java_demo_rpo -- %{debug_suffix_unquoted}}

%description demo-debug
The OpenJDK demos.
%{debug_warning}
%endif

%if %{include_normal_build}
%package src
Summary: OpenJDK Source Bundle
Group:   Development/Languages

%{java_src_rpo %{nil}}

%description src
The OpenJDK source bundle.
%endif

%if %{include_debug_build}
%package src-debug
Summary: OpenJDK Source Bundle %{for_debug}
Group:   Development/Languages

%{java_src_rpo -- %{debug_suffix_unquoted}}

%description src-debug
The OpenJDK source bundle %{for_debug}.
%endif

%if %{include_normal_build}
%package javadoc
Summary: OpenJDK API Documentation
Group:   Documentation
Requires: javapackages-tools
BuildArch: noarch

%{java_javadoc_rpo %{nil}}

%description javadoc
The OpenJDK API documentation.
%endif

%if %{include_normal_build}
%package javadoc-zip
Summary: OpenJDK API Documentation compressed in single archive
Group:   Documentation
Requires: javapackages-tools
BuildArch: noarch

%{java_javadoc_rpo %{nil}}

%description javadoc-zip
The OpenJDK API documentation compressed in single archive.
%endif

%if %{include_debug_build}
%package javadoc-debug
Summary: OpenJDK API Documentation %{for_debug}
Group:   Documentation
Requires: javapackages-tools
BuildArch: noarch

%{java_javadoc_rpo -- %{debug_suffix_unquoted}}

%description javadoc-debug
The OpenJDK API documentation %{for_debug}.
%endif

%if %{include_debug_build}
%package javadoc-zip-debug
Summary: OpenJDK API Documentation compressed in single archive %{for_debug}
Group:   Documentation
Requires: javapackages-tools
BuildArch: noarch

%{java_javadoc_rpo -- %{debug_suffix_unquoted}}

%description javadoc-zip-debug
The OpenJDK API documentation compressed in single archive %{for_debug}.
%endif


%if %{include_normal_build}
%package accessibility
Summary: OpenJDK accessibility connector

%{java_accessibility_rpo %{nil}}

%description accessibility
Enables accessibility support in OpenJDK by using java-atk-wrapper. This allows
compatible at-spi2 based accessibility programs to work for AWT and Swing-based
programs.

Please note, the java-atk-wrapper is still in beta, and OpenJDK itself is still
being tuned to be working with accessibility features. There are known issues
with accessibility on, so please do not install this package unless you really
need to.
%endif

%if %{include_debug_build}
%package accessibility-debug
Summary: OpenJDK accessibility connector %{for_debug}

%{java_accessibility_rpo -- %{debug_suffix_unquoted}}

%description accessibility-debug
See normal java-%{version}-openjdk-accessibility description.
%endif


%if %{with_openjfx_binding}
%package openjfx
Summary: OpenJDK x OpenJFX connector. This package adds symliks finishing Java FX integration to %{name}
Requires: %{name}%{?_isa} = %{epoch}:%{version}-%{release}
Requires: openjfx%{?_isa}
Provides: javafx  = %{epoch}:%{version}-%{release}
%description openjfx
Set of links from OpenJDK (jre) to OpenJFX

%package openjfx-devel
Summary: OpenJDK x OpenJFX connector for FX developers. This package adds symliks finishing Java FX integration to %{name}-devel
Requires: %{name}-devel%{?_isa} = %{epoch}:%{version}-%{release}
Requires: openjfx-devel%{?_isa}
Provides: javafx-devel = %{epoch}:%{version}-%{release}
%description openjfx-devel
Set of links from OpenJDK (sdk) to OpenJFX

%if %{include_debug_build}
%package openjfx-debug
Summary: OpenJDK x OpenJFX connector %{for_debug}. his package adds symliks finishing Java FX integration to %{name}-debug
Requires: %{name}-debug%{?_isa} = %{epoch}:%{version}-%{release}
Requires: openjfx%{?_isa}
Provides: javafx-debug = %{epoch}:%{version}-%{release}
%description openjfx-debug
Set of links from OpenJDK-debug (jre) to normal OpenJFX. OpenJFX do not support debug buuilds of itself

%package openjfx-devel-debug
Summary: OpenJDK x OpenJFX connector for FX developers %{for_debug}. This package adds symliks finishing Java FX integration to %{name}-devel-debug
Requires: %{name}-devel-debug%{?_isa} = %{epoch}:%{version}-%{release}
Requires: openjfx-devel%{?_isa}
Provides: javafx-devel-debug = %{epoch}:%{version}-%{release}
%description openjfx-devel-debug
Set of links from OpenJDK-debug (sdk) to normal OpenJFX. OpenJFX do not support debug buuilds of itself
%endif
%endif

%prep
if [ %{include_normal_build} -eq 0 -o  %{include_normal_build} -eq 1 ] ; then
  echo "include_normal_build is %{include_normal_build}"
else
  echo "include_normal_build is %{include_normal_build}, thats invalid. Use 1 for yes or 0 for no"
  exit 11
fi
if [ %{include_debug_build} -eq 0 -o  %{include_debug_build} -eq 1 ] ; then
  echo "include_debug_build is %{include_debug_build}"
else
  echo "include_debug_build is %{include_debug_build}, thats invalid. Use 1 for yes or 0 for no"
  exit 12
fi
if [ %{include_debug_build} -eq 0 -a  %{include_normal_build} -eq 0 ] ; then
  echo "you have disabled both include_debug_build and include_debug_build. no go."
  exit 13
fi
%setup -q -c -n %{uniquesuffix ""} -T -a 0
# https://bugzilla.redhat.com/show_bug.cgi?id=1189084
prioritylength=`expr length %{priority}`
if [ $prioritylength -ne 7 ] ; then
 echo "priority must be 7 digits in total, violated"
 exit 14
fi
# For old patches
ln -s openjdk jdk8
%if %{use_shenandoah_hotspot}
# On Shenandoah-supported architectures, replace HotSpot with
# the Shenandoah version
pushd openjdk
tar -xf %{SOURCE1}
rm -rf hotspot
mv openjdk/hotspot .
rm -rf openjdk
popd
%endif

cp %{SOURCE2} .

# replace outdated configure guess script
#
# the configure macro will do this too, but it also passes a few flags not
# supported by openjdk configure script
cp %{SOURCE100} openjdk/common/autoconf/build-aux/
cp %{SOURCE101} openjdk/common/autoconf/build-aux/

# OpenJDK patches

# Remove libraries that are linked
sh %{SOURCE12}

# System library fixes
%patch201
%patch202
%patch203

# Debugging fixes
%patch204
%patch205
%patch206
%patch207
%patch208
%patch209
%patch210

%patch1
%patch3
%patch5
%patch7

# s390 build fixes
%patch100
%patch102
%patch103

# ppc64le fixes

%patch603
%patch601
%patch602

# Zero fixes.

# Upstreamable fixes
%patch502
%patch504
%patch506
%patch507
%patch508
%patch509
%patch511
%patch512
%patch513
%patch514
%patch515
%patch516
%patch517
%patch518
%patch519
%patch400
%patch523
%patch526
%patch528
%patch532
%patch535
%patch538
%patch547
%patch550
%patch551
%patch553
%patch555
%patch560
%patch561

# PPC64 updates
%patch556
%patch557
%patch558
%patch559

# RPM-only fixes
%patch525
%patch539

# RHEL-only patches
%if ! 0%{?fedora} && 0%{?rhel} <= 7
%patch534
%endif

# 8175887 was added to the Shenandoah HotSpot ahead of time
%if %{use_shenandoah_hotspot}
%else
%patch554
%endif

%patch1000

# Extract systemtap tapsets
%if %{with_systemtap}
tar -x -I xz -f %{SOURCE8}
%if %{include_debug_build}
cp -r tapset tapset%{debug_suffix}
%endif


for suffix in %{build_loop} ; do
  for file in "tapset"$suffix/*.in; do
    OUTPUT_FILE=`echo $file | sed -e s:%{javaver}\.stp\.in$:%{version}-%{release}.%{_arch}.stp:g`
    sed -e s:@ABS_SERVER_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/jre/lib/%{archinstall}/server/libjvm.so:g $file > $file.1
# TODO find out which architectures other than i686 have a client vm
%ifarch %{ix86}
    sed -e s:@ABS_CLIENT_LIBJVM_SO@:%{_jvmdir}/%{sdkdir -- $suffix}/jre/lib/%{archinstall}/client/libjvm.so:g $file.1 > $OUTPUT_FILE
%else
    sed -e '/@ABS_CLIENT_LIBJVM_SO@/d' $file.1 > $OUTPUT_FILE
%endif
    sed -i -e s:@ABS_JAVA_HOME_DIR@:%{_jvmdir}/%{sdkdir -- $suffix}:g $OUTPUT_FILE
    sed -i -e s:@INSTALL_ARCH_DIR@:%{archinstall}:g $OUTPUT_FILE
    sed -i -e s:@prefix@:%{_jvmdir}/%{sdkdir -- $suffix}/:g $OUTPUT_FILE
  done
done
# systemtap tapsets ends
%endif

# Prepare desktop files
for suffix in %{build_loop} ; do
for file in %{SOURCE9} %{SOURCE10} ; do
    FILE=`basename $file | sed -e s:\.in$::g`
    EXT="${FILE##*.}"
    NAME="${FILE%.*}"
    OUTPUT_FILE=$NAME$suffix.$EXT
    sed -e s:#JAVA_HOME#:%{sdkbindir -- $suffix}:g $file > $OUTPUT_FILE
    sed -i -e  s:#JRE_HOME#:%{jrebindir -- $suffix}:g $OUTPUT_FILE
    sed -i -e  s:#ARCH#:%{version}-%{release}.%{_arch}$suffix:g $OUTPUT_FILE
done
done

# Setup nss.cfg
sed -e s:@NSS_LIBDIR@:%{NSS_LIBDIR}:g %{SOURCE11} > nss.cfg


%build
# How many cpu's do we have?
export NUM_PROC=%(/usr/bin/getconf _NPROCESSORS_ONLN 2> /dev/null || :)
export NUM_PROC=${NUM_PROC:-1}
%if 0%{?_smp_ncpus_max}
# Honor %%_smp_ncpus_max
[ ${NUM_PROC} -gt %{?_smp_ncpus_max} ] && export NUM_PROC=%{?_smp_ncpus_max}
%endif

# Build IcedTea and OpenJDK.
%ifarch s390x sparc64 alpha %{power64} %{aarch64}
export ARCH_DATA_MODEL=64
%endif
%ifarch alpha
export CFLAGS="$CFLAGS -mieee"
%endif

# We use ourcppflags because the OpenJDK build seems to
# pass EXTRA_CFLAGS to the HotSpot C++ compiler...
# Explicitly set the C++ standard as the default has changed on GCC >= 6
EXTRA_CFLAGS="%ourcppflags -std=gnu++98 -Wno-error -fno-delete-null-pointer-checks -fno-lifetime-dse"
EXTRA_CPP_FLAGS="%ourcppflags -std=gnu++98 -fno-delete-null-pointer-checks -fno-lifetime-dse"
%ifarch %{power64} ppc
# fix rpmlint warnings
EXTRA_CFLAGS="$EXTRA_CFLAGS -fno-strict-aliasing"
%endif
export EXTRA_CFLAGS

(cd openjdk/common/autoconf
 bash ./autogen.sh
)

for suffix in %{build_loop} ; do
if [ "$suffix" = "%{debug_suffix}" ] ; then
debugbuild=%{debugbuild_parameter}
else
debugbuild=%{normalbuild_parameter}
fi

mkdir -p %{buildoutputdir -- $suffix}
pushd %{buildoutputdir -- $suffix}

NSS_LIBS="%{NSS_LIBS} -lfreebl" \
NSS_CFLAGS="%{NSS_CFLAGS}" \
bash ../../configure \
%ifnarch %{jit_arches}
    --with-jvm-variants=zero \
%endif
    --disable-zip-debug-info \
    --with-milestone="fcs" \
    --with-update-version=%{updatever} \
    --with-build-number=%{buildver} \
    --with-boot-jdk=/usr/lib/jvm/java-openjdk \
    --with-debug-level=$debugbuild \
    --enable-unlimited-crypto \
    --enable-system-nss \
    --with-zlib=system \
    --with-libjpeg=system \
    --with-giflib=system \
    --with-libpng=system \
    --with-lcms=bundled \
    --with-stdc++lib=dynamic \
    --with-extra-cxxflags="$EXTRA_CPP_FLAGS" \
    --with-extra-cflags="$EXTRA_CFLAGS" \
    --with-extra-ldflags="%{ourldflags}" \
    --with-num-cores="$NUM_PROC"

cat spec.gmk
cat hotspot-spec.gmk

# The combination of FULL_DEBUG_SYMBOLS=0 and ALT_OBJCOPY=/does_not_exist
# disables FDS for all build configs and reverts to pre-FDS make logic.
# STRIP_POLICY=none says don't do any stripping. DEBUG_BINARIES=true says
# ignore all the other logic about which debug options and just do '-g'.

make \
    DEBUG_BINARIES=true \
    JAVAC_FLAGS=-g \
    STRIP_POLICY=no_strip \
    POST_STRIP_CMD="" \
    LOG=trace \
    SCTP_WERROR= \
    %{targets}

make zip-docs

# the build (erroneously) removes read permissions from some jars
# this is a regression in OpenJDK 7 (our compiler):
# http://icedtea.classpath.org/bugzilla/show_bug.cgi?id=1437
find images/%{j2sdkimage} -iname '*.jar' -exec chmod ugo+r {} \;
chmod ugo+r images/%{j2sdkimage}/lib/ct.sym

# remove redundant *diz and *debuginfo files
find images/%{j2sdkimage} -iname '*.diz' -exec rm {} \;
find images/%{j2sdkimage} -iname '*.debuginfo' -exec rm {} \;

popd >& /dev/null

# Install nss.cfg right away as we will be using the JRE above
export JAVA_HOME=$(pwd)/%{buildoutputdir -- $suffix}/images/%{j2sdkimage}

# Install nss.cfg right away as we will be using the JRE above
install -m 644 nss.cfg $JAVA_HOME/jre/lib/security/

# Use system-wide tzdata
rm $JAVA_HOME/jre/lib/tzdb.dat
ln -s %{_datadir}/javazi-1.8/tzdb.dat $JAVA_HOME/jre/lib/tzdb.dat

#build cycles
done

%check

# We test debug first as it will give better diagnostics on a crash
for suffix in %{rev_build_loop} ; do

export JAVA_HOME=$(pwd)/%{buildoutputdir -- $suffix}/images/%{j2sdkimage}

# Check unlimited policy has been used
$JAVA_HOME/bin/javac -d . %{SOURCE13}
$JAVA_HOME/bin/java TestCryptoLevel

# Check ECC is working
$JAVA_HOME/bin/javac -d . %{SOURCE14}
$JAVA_HOME/bin/java $(echo $(basename %{SOURCE14})|sed "s|\.java||")

# Check debug symbols are present and can identify code
find "$JAVA_HOME" -iname '*.so' -print0 | while read -d $'\0' lib
do
  if [ -f "$lib" ] ; then
    echo "Testing $lib for debug symbols"
    # All these tests rely on RPM failing the build if the exit code of any set
    # of piped commands is non-zero.

    # Test for .debug_* sections in the shared object. This is the  main test.
    # Stripped objects will not contain these.
    eu-readelf -S "$lib" | grep "] .debug_"
    test $(eu-readelf -S "$lib" | grep -E "\]\ .debug_(info|abbrev)" | wc --lines) == 2

    # Test FILE symbols. These will most likely be removed by anyting that
    # manipulates symbol tables because it's generally useless. So a nice test
    # that nothing has messed with symbols.
    old_IFS="$IFS"
    IFS=$'\n'
    for line in $(eu-readelf -s "$lib" | grep "00000000      0 FILE    LOCAL  DEFAULT")
    do
     # We expect to see .cpp files, except for architectures like aarch64 and
     # s390 where we expect .o and .oS files
      echo "$line" | grep -E "ABS ((.*/)?[-_a-zA-Z0-9]+\.(c|cc|cpp|cxx|o|oS))?$"
    done
    IFS="$old_IFS"

    # If this is the JVM, look for javaCalls.(cpp|o) in FILEs, for extra sanity checking.
    if [ "`basename $lib`" = "libjvm.so" ]; then
      eu-readelf -s "$lib" | \
        grep -E "00000000      0 FILE    LOCAL  DEFAULT      ABS javaCalls.(cpp|o)$"
    fi

    # Test that there are no .gnu_debuglink sections pointing to another
    # debuginfo file. There shouldn't be any debuginfo files, so the link makes
    # no sense either.
    eu-readelf -S "$lib" | grep 'gnu'
    if eu-readelf -S "$lib" | grep '] .gnu_debuglink' | grep PROGBITS; then
      echo "bad .gnu_debuglink section."
      eu-readelf -x .gnu_debuglink "$lib"
      false
    fi
  fi
done

# Make sure gdb can do a backtrace based on line numbers on libjvm.so
gdb -q "$JAVA_HOME/bin/java" <<EOF | tee gdb.out
handle SIGSEGV pass nostop noprint
handle SIGILL pass nostop noprint
set breakpoint pending on
break javaCalls.cpp:1
commands 1
backtrace
quit
end
run -version
EOF
grep 'JavaCallWrapper::JavaCallWrapper' gdb.out

# Check src.zip has all sources. See RHBZ#1130490
jar -tf $JAVA_HOME/src.zip | grep 'sun.misc.Unsafe'

# Check class files include useful debugging information
$JAVA_HOME/bin/javap -l java.lang.Object | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.lang.Object | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.lang.Object | grep LocalVariableTable

# Check generated class files include useful debugging information
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep "Compiled from"
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LineNumberTable
$JAVA_HOME/bin/javap -l java.nio.ByteBuffer | grep LocalVariableTable

#build cycles check
done

%install
STRIP_KEEP_SYMTAB=libjvm*

for suffix in %{build_loop} ; do

pushd %{buildoutputdir -- $suffix}/images/%{j2sdkimage}

#install jsa directories so we can owe them
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}/server/
mkdir -p $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}/client/

  # Install main files.
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}
  cp -a bin include lib src.zip $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}
  cp -a jre/bin jre/lib $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}

%if %{with_systemtap}
  # Install systemtap support files.
  install -dm 755 $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset
  # note, that uniquesuffix  is in BUILD dir in this case
  cp -a $RPM_BUILD_DIR/%{uniquesuffix ""}/tapset$suffix/*.stp $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
  pushd  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/tapset/
   tapsetFiles=`ls *.stp`
  popd
  install -d -m 755 $RPM_BUILD_ROOT%{tapsetdir}
  pushd $RPM_BUILD_ROOT%{tapsetdir}
    RELATIVE=$(%{abs2rel} %{_jvmdir}/%{sdkdir -- $suffix}/tapset %{tapsetdir})
    for name in $tapsetFiles ; do
      targetName=`echo $name | sed "s/.stp/$suffix.stp/"`
      ln -sf $RELATIVE/$name $targetName
    done
  popd
%endif

  # Remove empty cacerts database.
  rm -f $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}/lib/security/cacerts
  # Install cacerts symlink needed by some apps which hardcode the path.
  pushd $RPM_BUILD_ROOT%{_jvmdir}/%{jredir -- $suffix}/lib/security
    RELATIVE=$(%{abs2rel} %{_sysconfdir}/pki/java \
      %{_jvmdir}/%{jredir -- $suffix}/lib/security)
    ln -sf $RELATIVE/cacerts .
  popd

  # Install JCE policy symlinks.
  install -d -m 755 $RPM_BUILD_ROOT%{_jvmprivdir}/%{uniquesuffix -- $suffix}/jce/vanilla

  # Install versioned symlinks.
  pushd $RPM_BUILD_ROOT%{_jvmdir}
    ln -sf %{jredir -- $suffix} %{jrelnk -- $suffix}
  popd

  # Remove javaws man page
  rm -f man/man1/javaws*

  # Install man pages.
  install -d -m 755 $RPM_BUILD_ROOT%{_mandir}/man1
  for manpage in man/man1/*
  do
    # Convert man pages to UTF8 encoding.
    iconv -f ISO_8859-1 -t UTF8 $manpage -o $manpage.tmp
    mv -f $manpage.tmp $manpage
    install -m 644 -p $manpage $RPM_BUILD_ROOT%{_mandir}/man1/$(basename \
      $manpage .1)-%{uniquesuffix -- $suffix}.1
  done

  # Install demos and samples.
  cp -a demo $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}
  mkdir -p sample/rmi
  if [ ! -e sample/rmi/java-rmi.cgi ] ; then 
    # hack to allow --short-circuit on install
    mv bin/java-rmi.cgi sample/rmi
  fi
  cp -a sample $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}

popd


# Install Javadoc documentation.
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}
cp -a %{buildoutputdir -- $suffix}/docs $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}
cp -a %{buildoutputdir -- $suffix}/bundles/jdk-%{javaver}_%{updatever}$suffix-%{buildver}-docs.zip  $RPM_BUILD_ROOT%{_javadocdir}/%{uniquejavadocdir -- $suffix}.zip

# Install icons and menu entries.
for s in 16 24 32 48 ; do
  install -D -p -m 644 \
    openjdk/jdk/src/solaris/classes/sun/awt/X11/java-icon${s}.png \
    $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${s}x${s}/apps/java-%{javaver}.png
done

# Install desktop files.
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/{applications,pixmaps}
for e in jconsole$suffix policytool$suffix ; do
    desktop-file-install --vendor=%{uniquesuffix -- $suffix} --mode=644 \
        --dir=$RPM_BUILD_ROOT%{_datadir}/applications $e.desktop
done

# Install /etc/.java/.systemPrefs/ directory
# See https://bugzilla.redhat.com/show_bug.cgi?id=741821
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/.java/.systemPrefs

# FIXME: remove SONAME entries from demo DSOs.  See
# https://bugzilla.redhat.com/show_bug.cgi?id=436497

# Find non-documentation demo files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/sample \
  -type f -o -type l | sort \
  | grep -v README \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  >> %{name}-demo.files"$suffix"
# Find documentation demo files.
find $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/demo \
  $RPM_BUILD_ROOT%{_jvmdir}/%{sdkdir -- $suffix}/sample \
  -type f -o -type l | sort \
  | grep README \
  | sed 's|'$RPM_BUILD_ROOT'||' \
  | sed 's|^|%doc |' \
  >> %{name}-demo.files"$suffix"

# Create links which leads to separately installed java-atk-bridge and allow configuration
# links points to java-atk-wrapper - an dependence
  pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}
    ln -s %{_libdir}/java-atk-wrapper/libatk-wrapper.so.0 libatk-wrapper.so
  popd
  pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/ext
     ln -s %{_libdir}/java-atk-wrapper/java-atk-wrapper.jar  java-atk-wrapper.jar
  popd
  pushd $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/
    echo "#Config file to  enable java-atk-wrapper" > accessibility.properties
    echo "" >> accessibility.properties
    echo "assistive_technologies=org.GNOME.Accessibility.AtkWrapper" >> accessibility.properties
    echo "" >> accessibility.properties
  popd

# intentionally after all else, fx links  with redirections on its own
%if %{with_openjfx_binding}
  FXSDK_FILES=%{name}-openjfx-devel.files"$suffix"
  FXJRE_FILES=%{name}-openjfx.files"$suffix"
  echo -n "" > $FXJRE_FILES
  echo -n "" > $FXSDK_FILES
  for file in  %{jfx_jre_libs} ; do
    srcfile=%{jfx_jre_libs_dir}/$file
    targetfile=%{_jvmdir}/%{jredir -- $suffix}/lib/$file
    ln -s $srcfile $RPM_BUILD_ROOT/$targetfile
    echo $targetfile >> $FXJRE_FILES
  done
  for file in  %{jfx_jre_native} ; do
    srcfile=%{jfx_jre_native_dir}/$file
    targetfile=%{_jvmdir}/%{jredir -- $suffix}/lib/%{archinstall}/$file
    ln -s $srcfile $RPM_BUILD_ROOT/$targetfile
    echo $targetfile >> $FXJRE_FILES
  done
  for file in  %{jfx_jre_exts} ; do
    srcfile=%{jfx_jre_exts_dir}/$file
    targetfile=%{_jvmdir}/%{jredir -- $suffix}/lib/ext/$file
    ln -s $srcfile $RPM_BUILD_ROOT/$targetfile
    echo $targetfile >> $FXJRE_FILES
  done
  for file in  %{jfx_sdk_libs} ; do
    srcfile=%{jfx_sdk_libs_dir}/$file
    targetfile=%{_jvmdir}/%{sdkdir -- $suffix}/lib/$file
    ln -s $srcfile $RPM_BUILD_ROOT/$targetfile
    echo $targetfile >> $FXSDK_FILES
  done
  for file in  %{jfx_sdk_bins} ; do
    srcfile=%{jfx_sdk_bins_dir}/$file
    targetfile=%{_jvmdir}/%{sdkdir -- $suffix}/bin/$file
    ln -s $srcfile $RPM_BUILD_ROOT/$targetfile
    echo $targetfile >> $FXSDK_FILES
  done
%endif

bash %{SOURCE20} $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix} %{javaver}
# https://bugzilla.redhat.com/show_bug.cgi?id=1183793
touch -t 201401010000 $RPM_BUILD_ROOT/%{_jvmdir}/%{jredir -- $suffix}/lib/security/java.security

# end, dual install
done

%if %{include_normal_build} 
# intentioanlly only for non-debug
%pretrans headless -p <lua>
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue
-- see https://bugzilla.redhat.com/show_bug.cgi?id=1290388 for pretrans over pre
-- if copy-jdk-configs is in transaction, it installs in pretrans to temp
-- if copy_jdk_configs is in temp, then it means that copy-jdk-configs is in tranasction  and so is
-- preferred over one in %%{_libexecdir}. If it is not in transaction, then depends 
-- whether copy-jdk-configs is installed or not. If so, then configs are copied
-- (copy_jdk_configs from %%{_libexecdir} used) or not copied at all
local posix = require "posix"
local debug = false

SOURCE1 = "%{rpm_state_dir}/copy_jdk_configs.lua"
SOURCE2 = "%{_libexecdir}/copy_jdk_configs.lua"

local stat1 = posix.stat(SOURCE1, "type");
local stat2 = posix.stat(SOURCE2, "type");

  if (stat1 ~= nil) then
  if (debug) then
    print(SOURCE1 .." exists - copy-jdk-configs in transaction, using this one.")
  end;
  package.path = package.path .. ";" .. SOURCE1
else 
  if (stat2 ~= nil) then
  if (debug) then
    print(SOURCE2 .." exists - copy-jdk-configs alrady installed and NOT in transation. Using.")
  end;
  package.path = package.path .. ";" .. SOURCE2
  else
    if (debug) then
      print(SOURCE1 .." does NOT exists")
      print(SOURCE2 .." does NOT exists")
      print("No config files will be copied")
    end
  return
  end
end
-- run contetn of included file with fake args
arg = {"--currentjvm", "%{uniquesuffix %{nil}}", "--jvmdir", "%{_jvmdir %{nil}}", "--origname", "%{name}", "--origjavaver", "%{javaver}", "--arch", "%{_arch}", "--temp", "%{rpm_state_dir}/%{name}.%{_arch}"}
require "copy_jdk_configs.lua"

%post 
%{post_script %{nil}}

%post headless
%{post_headless %{nil}}

%postun
%{postun_script %{nil}}

%postun headless
%{postun_headless %{nil}}

%posttrans
%{posttrans_script %{nil}}

%post devel
%{post_devel %{nil}}

%postun devel
%{postun_devel %{nil}}

%posttrans  devel
%{posttrans_devel %{nil}}

%post javadoc
%{post_javadoc %{nil}}

%postun javadoc
%{postun_javadoc %{nil}}

%post javadoc-zip
%{post_javadoc_zip %{nil}}

%postun javadoc-zip
%{postun_javadoc_zip %{nil}}
%endif

%if %{include_debug_build} 
%post debug
%{post_script -- %{debug_suffix_unquoted}}

%post headless-debug
%{post_headless -- %{debug_suffix_unquoted}}

%postun debug
%{postun_script -- %{debug_suffix_unquoted}}

%postun headless-debug
%{postun_headless -- %{debug_suffix_unquoted}}

%posttrans debug
%{posttrans_script -- %{debug_suffix_unquoted}}

%post devel-debug
%{post_devel -- %{debug_suffix_unquoted}}

%postun devel-debug
%{postun_devel -- %{debug_suffix_unquoted}}

%posttrans  devel-debug
%{posttrans_devel -- %{debug_suffix_unquoted}}

%post javadoc-debug
%{post_javadoc -- %{debug_suffix_unquoted}}

%postun javadoc-debug
%{postun_javadoc -- %{debug_suffix_unquoted}}

%post javadoc-zip-debug
%{post_javadoc_zip -- %{debug_suffix_unquoted}}

%postun javadoc-zip-debug
%{postun_javadoc_zip -- %{debug_suffix_unquoted}}
%endif

%if %{include_normal_build} 
%files
# main package builds always
%{files_jre %{nil}}
%else
%files
# placeholder
%endif


%if %{include_normal_build} 
%files headless
# important note, see https://bugzilla.redhat.com/show_bug.cgi?id=1038092 for whole issue 
# all config/norepalce files (and more) have to be declared in pretrans. See pretrans
%{files_jre_headless %{nil}}

%files devel
%{files_devel %{nil}}

%files demo -f %{name}-demo.files
%{files_demo %{nil}}

%files src
%{files_src %{nil}}

%files javadoc
%{files_javadoc %{nil}}

%files javadoc-zip
%{files_javadoc_zip %{nil}}

%files accessibility
%{files_accessibility %{nil}}

%if %{with_openjfx_binding}
%files openjfx -f %{name}-openjfx.files

%files openjfx-devel -f %{name}-openjfx-devel.files
%endif
%endif

%if %{include_debug_build} 
%files debug
%{files_jre -- %{debug_suffix_unquoted}}

%files headless-debug
%{files_jre_headless -- %{debug_suffix_unquoted}}

%files devel-debug
%{files_devel -- %{debug_suffix_unquoted}}

%files demo-debug -f %{name}-demo.files-debug
%{files_demo -- %{debug_suffix_unquoted}}

%files src-debug
%{files_src -- %{debug_suffix_unquoted}}

%files javadoc-debug
%{files_javadoc -- %{debug_suffix_unquoted}}

%files javadoc-zip-debug
%{files_javadoc_zip -- %{debug_suffix_unquoted}}

%files accessibility-debug
%{files_accessibility -- %{debug_suffix_unquoted}}

%if %{with_openjfx_binding}
%files openjfx-debug -f %{name}-openjfx.files-debug

%files openjfx-devel-debug -f %{name}-openjfx-devel.files-debug
%endif
%endif

%changelog
* Mon Nov 13 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.151-1.b12
- added ownership of etc dirs
- sysconfdir/.java/.systemPrefs
- sysconfdir/.java

* Wed Oct 25 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.151-1.b12
- updated to aarch64-jdk8u151-b12 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u151-b12 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u151-b12.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u151-b12.tar.xz as new sources for hotspot
- tapset updated to 3.6pre02
- policies adapted to new limited/unlimited schmea
- above acomapnied by c-j-c 3.3
- alligned patches and added PPC ones (thanx to gnu_andrew)
- added patch209: 8035496-hotspot.patch
- added patch210: suse_linuxfilestore.patch

* Wed Oct 04 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.144-7.b01
- updated to aarch64-shenandoah-jdk8u144-b02-shenandoah-merge-2017-10-02 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u144-b02-shenandoah-merge-2017-10-02.tar.xz as new sources for hotspot

* Fri Sep 15 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-6.b01
- added patch540, bug1484079.patch

* Fri Sep 08 2017 Troy Dawson <tdawson@redhat.com> - 1:1.8.0.144-6.b01
- Cleanup spec file conditionals

* Fri Aug 25 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-4.b01
- added ownership of diretories which were oonly listing files

* Fri Aug 25 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-3.b01
- added (experiment) "--" delimiter also to $suffix in expanding macros

* Wed Aug 23 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.144-1.b01
- Update to aarch64-jdk8u144-b01 and aarch64-shenandoah-jdk8u144-b01.
- Exclude 8175887 from Shenandoah builds as it has been included in that repo.
- Added 8164293-pr3412-rh1459641.patch backport from 8u development tree
- get rid of bin/* and lib/*, fixed rhbz1480777
- adapted to rpm 4.14: all expanding macros changed to define, all %1 and %%1 replaced by %{?1}, all expandable macros parameter preffixed by --
- get rid of generated filelists all except javafx and demos

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.141-5.b16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Sun Jul 30 2017 Florian Weimer <fweimer@redhat.com> - 1:1.8.0.141-4.b16
- Rebuild with binutils fix for ppc64le (#1475636)

* Wed Jul 26 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.141-3.b16
- added patch208, aarch64BuildFailure.patch to fix condition found during jdk9 build

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1:1.8.0.141-2.b16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Jul 21 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.141-1.b16
- updated to security u141.b16
- sync patches with rhel7
- removed no longer defined jvmjardir

* Sat Jun 17 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-7.b12
- adapted to no longer noarch openjfx-devel

* Wed Jun 07 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-6.b12
- added virtualprovides for javafx

* Wed Jun 07 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-5.b12
- fixed target of to fxrt.jar link
- fixedname of libglass

* Tue Jun 06 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-3.b12
- source999 moved to source1
- added two pathces 8181055-pr3394-rh1448880.patch and 8175813/PR3394/RH1448880
- enabled (commented out) system NSS via patch1000, enableCommentedOutSystemNss.patch

* Tue May 09 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-1.b12
- added javafx binding subpackages

* Thu Apr 20 2017 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.131-1.b12
- updated to aarch64-jdk8u131-b12 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u131-b12-shenandoah-merge-2017-04-20 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u131-b12.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u131-b12-shenandoah-merge-2017-04-20.tar.xz as new sources for hotspot

* Sun Mar 19 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-12.b14
- minor tweaks, egrep replaced by grep -E, added provides for some subpackages

* Mon Mar 13 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-11.b14
- sync from rhel, reordered patches, enabled shenanoah on aarch64
- Patch OpenJDK to check the system cacerts database directly
- Remove unneeded symlink to the system cacerts database
- Drop outdated openssl dependency from when the RPM built the cacerts database
- udpated to latest stable shenandoah hotspot

* Mon Mar 13 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-10.b14
- rhbz#1423751 - removed -fno-split-loops worakround as building against newer GCC7

* Tue Feb 28 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-9.b14
- updated to latest stable shenandoah hotspot
- updated to properly tagged upstream forest (no update, just rename)
- fixed update package to verify PR2126 patch and work with sha512

* Tue Feb 28 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-8.b14
- rebuild because of NSS

* Tue Feb 21 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-7.b14
- fixed the config(noreplace) issue with various left files lke java.security (rhbz#1183793)
- by calling new c-j-c hooks
- removed self-tail-bitting check check_sum_presented_in_spec
- release 6+7 to verify update path

* Mon Feb 20 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-5.b14
- patch 536 reordered to 537
- added patch 536 - Backport "8170888: [linux] Experimental support for cgroup memory limits in container (ie Docker) environments"
- added patch 538 - 1423421: Javadoc crashes when method name ends with "Property"
- rhbz#1423751 - added -fno-split-loops worakround sigsew when building with GCC7 (probably bug in jdk's JIT )

* Fri Feb 17 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-4.b14
- added Patch535 and 526
- tweeked debugsymbols check for sigill

* Wed Jan 25 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-2.b14
- revertrd patch535, excludeECDHE-1415137.patch and related changes
- issue casued by nss, see rhbz#1415137 c#35

* Tue Jan 24 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-2.b14
- added patch535, excludeECDHE-1415137.patch to tmp-worakround crash with nss

* Tue Jan 24 2017 jvanek <jvanek@redhat.com> - 1:1.8.0.121-1.b14
- updated to aarch64-jdk8u121-b14 (from openjdk8-forests/latest-aarch64)
- updated to aarch64-shenandoah-jdk8u121-b14 (from openjdk8-forests/latest-shenandoah) of hotspot
- used openjdk8-forests-latest-aarch64-aarch64-jdk8u121-b14.tar.xz as new sources
- used openjdk8-forests-latest-shenandoah-aarch64-shenandoah-jdk8u121-b14.tar.xz as new sources for hotspot
- deleted:    8044762-pr2960.patch 8049226-pr2960.patch 8154210.patch 8158260-pr2991-rh1341258.patch 8159244-pr3074.patch
- adapted java-1.8.0-openjdk-size_t.patch pr1834-rh1022017.patch rh1163501.patch
- updated from internal (rhel) repo  OPENJDK_URL_DEFAULT=ssh://t...redhat.com//...ty/
- with custom PR2126=/.../pr2126.patch (removed newly added brainpool curves)
- withspecial values of PROJECT_NAME="openjdk8-forests", REPO_NAME="latest-aarch64"
- with correct tag VERSION="aarch64-jdk8u121-b14"
- and for shenandoah hotspot used custom repo REPO_NAME=latest-shenandoah
- with correct tag VERSION="aarch64-shenandoah-jdk8u121-b14"
- complete changes to  generate_source_tarball.sh  update_package.sh NOT commited (willbe regenerated from official repos soon)

* Mon Jan 09 2017 jvanek <jvanek@redhat.com - 1:1.8.0.111-5.b16
- Added arched dependencies to headless/main package

* Thu Nov 03 2016 jvanek <jvanek@redhat.com - 1:1.8.0.111-3.b16
- added patch207 - PR3183.patch
- java SSL/TLS implementation: should follow the policies of system-wide crypto policy 

* Fri Oct 21 2016 Omair Majid <omajid@redhat.com> - 1:1.8.0.111-2.b16
- added dont-add-unnecessary-debug-links.patch
- added hotspot-assembler-debuginfo.patch
- returned accidentally removed  hotspot-remove-debuglink.patch
- eu-readelfs on libraries improved, added gdb call

* Wed Oct 19 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.111-1.b16
- updated to aarch64-jdk8u111-b16 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u111-b16 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u111-b16.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u111-b16.tar.xz as new sources for hotspot
- adapted patches

* Wed Oct 5 2016  Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.102-3.b14
- debug subpackages allowed on aarch64 and ppc64le
- fontconfig and nss restricted by isa

* Wed Aug 31 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.102-2.b14
- declared check_sum_presented_in_spec and used in prep and check
- it is checking that latest packed java.security is mentioned in listing
- @prefix@ in tapsetfiles substitued by prefix as necessary to work with systemtap3 (rhbz1371005)

* Thu Aug 25 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.102-1.b14
- updated to aarch64-jdk8u102-b14 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u102-b14 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u102-b14.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u102-b14.tar.xz as new sources for hotspot
- removed upstreamed patches 519, 520 and 605
- updated to systemtap 3, removed related patches 300 and 301
- jjs provides moved to headless

* Mon Aug 01 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.101-3.b14
- Replace patch for S8162384 with upstream version. Document correctly along with SystemTap RH1204159 patch.
- Resolves: rhbz#1358661
- Replace patch for S8157306 with upstream version, documented & applied on all archs with conditional in patch
- Resolves: rhbz#1360863

* Mon Jul 25 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.101-2.b14
- added patch532 hotspot-1358661.patch - to fix performance of bimorphic inlining may be bypassed by type speculation
- added patch301 bz1204159_java8.patch - to fix systemtap on multiple jdks

* Mon Jul 25 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.101-1.b14
- updated to aarch64-jdk8u101-b14 (from aarch64-port/jdk8u)
- updated to aarch64-shenandoah-jdk8u101-b14-shenandoah-merge-2016-07-25 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-aarch64-jdk8u101-b14.tar.xz as new sources
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u101-b14-shenandoah-merge-2016-07-25.tar.xz as new sources for hotspot
- priority lowered for ine zero digit, tip moved to 999
- added 6260348-pr3066.patch, pr3083-rh1346460.patch, 8159244-pr3074.patch, corba_typo_fix.patch
renamed: jdk8-archivedJavadoc.patch -> 8154313.patch, pr2991-rh1341258.patch -> 8158260-pr2991-rh1341258.patch
- not added 8147771-additional_hunk.patch, already in b14

* Tue Jul 12 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.92-5.b14
- added Provides: /usr/bin/jjs

* Tue Jun 21 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.92-2.b14
- family restricted by arch

* Tue Jun 07 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.92-1.b14
- updated to u92
- removed upstreamed patches 8132051-aarch64.patch, 8143855.patch, criticalShenandoahFix.patch, rhbz1206656_fix_current_stack_pointer.patch
- 8132051-zero.patch, remove_aarch64_template_for_gcc6.patch
- jdwpCrash.abrt.patch renamed to 8044762-pr2960.patch
- httpsFix1329342.patch renamed to pr2934.patch
- added known regresisonos fixes for u92 scheduled for next u (519-525)

* Thu May 19 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-7.b14
- added patch519, jdwpCrash.abrt.patch to fix trasnportation error

* Fri May 13 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-6.b14
- Enable weak reference discovery in ShenandoahMarkCompact. Otherwise we never process any weak references in full-gc. 

* Tue May 03 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-5.b14
- Restricted to depend on exactly same version of nss as used for build
- Resolves: rhbz#1332456

* Tue May 03 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.91-4.b14
- updated to aarch64-shenandoah-jdk8u71-b15-beta02 (from aarch64-port/jdk8u-shenandoah) of hotspot
- used aarch64-port-jdk8u-shenandoah-aarch64-shenandoah-jdk8u71-b15-beta02.tar.xz as new sources for hotspot
- reverted  nss version fix

* Mon Apr 25 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.91-4.b14
- Restricted to depend on exactly same version of nss as use dfor build
- Resolves: rhbz#1332456

* Mon Apr 25 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.91-3.b14
- included shenandoah support in 64b intel

* Sun Apr 24 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.91-2.b14
- added patch518 httpsFix1329342.patch
- test based on SOURCE14 enabled
- Resolves: rhbz#1329342

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Roll back release number as release 1 never succeeded, even with tests disabled.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add additional fix to Zero patch to properly handle result on 64-bit big-endian
- Revert debugging options (aarch64 back to JIT, product build, no -Wno-error)
- Enable full bootstrap on all architectures to check we are good to go.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Turn tests back on or build will not fail.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Temporarily remove power64 from JIT arches to see if endian issue appears on Zero.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Turn off Java-based checks in a vain attempt to get a complete build.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Turn off -Werror so s390 can build in slowdebug mode.
- Add fix for formatting issue found by previous s390 build.
- Resolves: rhbz#1325423

* Tue Apr 12 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Revert settings to production defaults so we can at least get a build.
- Switch to a slowdebug build to try and unearth remaining issue on s390x.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Disable ECDSA test for now until failure on RHEL 7 is fixed.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add 8132051 port to Zero.
- Turn on bootstrap build for all to ensure we are now good to go.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Add 8132051 port to AArch64.
- Resolves: rhbz#1325423

* Mon Apr 11 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Enable a full bootstrap on JIT archs. Full build held back by Zero archs anyway.
- Resolves: rhbz#1325423

* Sun Apr 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Use basename of test file to avoid misinterpretation of full path as a package
- Resolves: rhbz#1325423

* Sun Apr 10 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.91-1.b14
- Update to u91b14.
- Resolves: rhbz#1325423

* Mon Apr 04 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.77-2.b03
- added patch400  jdk8-archivedJavadoc.patch
- added javadoc-zip(-debug) subpackage with compressed javadoc

* Thu Mar 31 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-3.b03
- Fix typo in test invocation.
- Resolves: rhbz#1245810

* Thu Mar 31 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-3.b03
- Add ECDSA test to ensure ECC is working.
- Resolves: rhbz#1245810

* Wed Mar 30 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-2.b03
- Avoid WithSeed versions of NSS functions as they do not fully process the seed
- List current java.security md5sum so that java.security is replaced and ECC gets enabled.
- Resolves: rhbz#1245810

* Wed Mar 23 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.77-1.b03
- Update to u77b03.

* Thu Mar 03 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-13.b16
- When using a compositing WM, the overlay window should be used, not the root window.

* Mon Feb 29 2016 Omair Majid <omajid@redhat.com> - 1:1.8.0.72-12.b15
- Use a simple backport for PR2462/8074839.
- Don't backport the crc check for pack.gz. It's not tested well upstream.

* Mon Feb 29 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-5.b16
- Fix regression introduced on s390 by large code cache change.
- Update to u72b16.
- Drop 8147805 and jvm.cfg fix which are applied upstream.

* Wed Feb 24 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-11.b15
- Add patches to allow the SunEC provider to be built with the system NSS install.
- Re-generate source tarball so it includes ecc_impl.h.
- Adjust tarball generation script to allow ecc_impl.h to be included.
- Bring over NSS changes from java-1.7.0-openjdk spec file (NSS_CFLAGS/NSS_LIBS)
- Remove patch which disables the SunEC provider as it is now usable.
- Correct spelling mistakes in tarball generation script.
- Move completely unrelated AArch64 gcc 6 patch into separate file.
- Resolves: rhbz#1019554 (fedora bug)

* Tue Feb 23 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-10.b15
- returning accidentlay removed hunk from renamed and so wrongly merged remove_aarch64_jvm.cfg_divergence.patch

* Mon Feb 22 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-9.b15
- sync from rhel

* Tue Feb 16 2016 Dan Horák <dan[at]danny.cz> - 1:1.8.0.72-8.b15
- Refresh s390-java-opts patch

* Tue Feb 16 2016 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.72-7.b15
- Use -fno-lifetime-dse over -fno-guess-branch-probability.
  See RHBZ#1306558.

* Mon Feb 15 2016 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.72-6.b15
- Add aarch64_FTBFS_rhbz_1307224.patch so as to resolve RHBZ#1307224.

* Fri Feb 12 2016 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.72-5.b15
- Add -fno-delete-null-pointer-checks -fno-guess-branch-probability flags to resolve x86/x86_64 crash.

* Mon Feb 08 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.72-5.b15
- Explicitly set the C++ standard to use, as the default has changed to C++ 2014 in GCC 6.
- Turn off -Werror due to format warnings in HotSpot and -std usage warnings in SCTP.
- Run tests under the check stage and use the debug build first.

* Fri Feb 05 2016 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.71-4.b15
- Backport S8148351: Only display resolved symlink for compiler, do not change path

* Wed Feb 03 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-3.b15
* touch -t 201401010000 java.security to try to worakround md5sums

* Wed Jan 27 2016 jvanek <jvanek@redhat.com> - 1:1.8.0.72-1.b15
- updated to aarch64-jdk8u72-b15 (from aarch64-port/jdk8u)
- used aarch64-port-jdk8u-aarch64-jdk8u72-b15.tar.xz as new sources
- removed already upstreamed patch501 8146566.patch

* Wed Jan 20 2016 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.71-1.b15
- sync with rhel7
- security update to CPU 19.1.2016 to u71b15

* Tue Dec 15 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-14.b17
- pretrans moved back to lua nd now includes file from copy-jdk-configs instead of call it

* Tue Dec 15 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.65-13.b17
- Disable hardened build on non-JIT arches.
  Workaround for RHBZ#1290936.

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-12.b17
-removed patch4 java-1.8.0-openjdk-PStack-808293.patch
-removed patch13 libjpeg-turbo-1.4-compat.patch

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-11.b17
- Define our own optimisation flags based on the optflags macro and pass to OpenJDK build cflags/cxxflags.
- Remove -fno-devirtualize as we are now on GCC 5 where the GCC bug it worked around is fixed.
- Pass __global_ldflags to --with-extra-ldflags so Fedora linker flags are used in the build.
- Also Pass ourcppflags to the OpenJDK build cflags as it wrongly uses them for the HotSpot C++ build.
- Add PR2428, PR2462 & S8143855 patches to fix build issues that arise.
- Resolves: rhbz#1283949
- Resolves: rhbz#1120792

* Thu Dec 10 2015 Andrew Hughes <gnu.andrew@redhat.com> - 1:1.8.0.65-10.b17
- Add patch to honour %%{_smp_ncpus_max} from Tuomo Soini
- Resolves: rhbz#1152896

* Wed Dec 09 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-9.b17
- extracted lua scripts moved from pre where they don't work to pretrans
- requirement on copy-jdk-configs made Week.

* Tue Dec 08 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-8.b17
- used extracted lua scripts.
- now depnding on copy-jdk-configs
- config files persisting in pre instead of %pretrans

* Tue Dec 08 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-7.b17
- changed way of generating the sources. As result:
- "updated" to aarch64-jdk8u65-b17 (from aarch64-port/jdk8u60)
- used aarch64-port-jdk8u60-aarch64-jdk8u65-b17.tar.xz as new sources

* Fri Nov 27 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-5.b17
- added missing md5sums
- moved to bundeld lcms

* Wed Nov 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-4.b17
- debug packages priority lowered by 1

* Wed Nov 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-3.b17
- depends on chkconfig >1.7 - added --family support

* Fri Nov 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-2.b17
- added and applied patch605 soundFontPatch.patch as repalcement for removed sound font links
- removed hardcoded soundfont links

* Thu Nov 12 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.65-1.b17
- updated to u65b17

* Mon Nov 09 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-17.b28
- policytool  manpage followed the binary from devel to jre

* Mon Nov 02 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-16.b28
added and applied patch604: aarch64-ifdefbugfix.patch to fix rhbz1276959

* Thu Oct 15 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-15.b28
- moved to single source integration forest
- removed patch patch9999 enableArm64.patch
- removed patch patch600  %%{name}-rh1191652-hotspot.patch

* Thu Aug 27 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-14.b24
- updated aarch64 tarball to contain whole forest of latest jdk8-aarch64-jdk8u60-b24.2.tar.xz
- using this forest instead of only hotspot
- generate_source_tarball.sh - temporarily excluded repos="hotspot" compression of download
- not only openjdk/hotspot is replaced, by wholeopenjdk
- ln -s openjdk jdk8 done after replacing of openjdk
- patches 9999 601 and 602 exclded for aarch64

* Wed Aug 26 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-13.b24
- updated aarch64 hotpost to latest jdk8-aarch64-jdk8u60-b24.2.tar.xz

* Wed Aug 19 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-12.b24
- updated to freshly released jdk8u60-jdk8u60-b27

* Thu Aug 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-11.b24
- another touching attempt to polycies...

* Mon Aug 03 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-10.b24
- arch64 updated to u60-b24 with hope to fix rhbz1249037

* Fri Jul 17 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-3.b24
- added one more md5sum test (thanx to Severin!)
 - I guess one more missing
- doubled slash in md5sum test in post

* Thu Jul 16 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-2.b24
- updated to security u60-b24
- moved to openjdk instead of jdk8 topdir in sources
- removed upstreamed patch99 java-1.8.0-openjdk-linux-4.x.patch
- removed upstreamed patch503 pr2444.patch
- removed upstreamed patch505 1208369_memory_leak_gcc5.patch
- removed upstreamed patch506: gif4.1.patch
 - note: usptream version is suspicious
  GIFLIB_MAJOR >= 5 SplashStreamGifInputFunc, NULL
  ELSE SplashStreamGifInputFunc
 - but the condition seems to be viceversa


* Mon Jun 22 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.60-7.b16
- Require javapackages-tools instead of jpackage-utils.

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.0.60-6.b16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 09 2015 Dan Horák <dan[at]danny.cz> - 1:1.8.0.60-5.b16
- allow build on Linux 4.x kernel
- refresh s390 size_t patch

* Fri Jun 05 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-4.b16
- added requires lksctp-tools for headless subpackage to make sun.nio.ch.sctp work

* Mon May 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-2.b16
- Patch503 d318d83c4e74.patch, patch505 1208369_memory_leak_gcc5.patch (and patch506 gif4.1.patch)
   moved out of "if with_systemtap" block

* Mon May 25 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.60-1.b16
- updated to u60b16
- deleted upstreamed patches:
   patch501 1182011_JavaPrintApiDoesNotPrintUmlautCharsWithPostscriptOutputCorrectly.patch
   patch502 1182694_javaApplicationMenuMisbehave.patch
   patch504 1210739_dns_naming_ipv6_addresses.patch
   patch402 atomic_linux_zero.inline.hpp.patch
   patch401 fix_ZERO_ARCHDEF_ppc.patch
   patch400 ppc_stack_overflow_fix.patch
   patch204 zero-interpreter-fix.patch
- added Patch506 gif4.1.patch to allow build agaisnt giflib > 4.1

* Wed May 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-38.b14
- updated to 8u45-b14 with hope to fix rhbz#1123870

* Wed May 13 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-37.b13
- added runtime requires for tzdata
- Remove reference to tz.properties which is no longer used (by gnu.andrew)

* Wed Apr 29 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.45-36.b13
- Patch hotspot to not use undefined code rather than passing
  -fno-tree-vrp via CFLAGS.
  Resolves: RHBZ#1208369
- Add upstream patch for DNS nameserver issue with IPv6 addresses.
  Resolves: RHBZ#1210739

* Wed Apr 29 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-35.b13
- Omit jsa files from power64 file list as well, as they are never generated
- moved to boot build by openjdk8
- Use the template interpreter on ppc64le

* Fri Apr 10 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-31.b13
- repacked sources

* Tue Apr 07 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.45-30.b13
- updated to security u45
- removed patch6: disable-doclint-by-default.patch
- added patch d318d83c4e74.patch
- added  rhbz1206656_fix_current_stack_pointer.patch
- renamed PStack-808293.patch -> java-1.8.0-openjdk-PStack-808293.patch
- renamed remove-intree-libraries.sh -> java-1.8.0-openjdk-remove-intree-libraries.sh
- renamed to preven conflix with jdk7

* Fri Apr 03 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-27.b25
- Add -fno-tree-vrp to flags to prevent hotspot miscompilation.
- Resolves: RHBZ#1208369

* Thu Apr 02 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-27.b25
- bumped release. Needed rebuild by itself on arm

* Tue Mar 31 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.40-26.b25
- Make Zero build-able on ARM32.
  Resolves: RHBZ#1206656

* Fri Mar 27 2015 Dan Horák <dan[at]danny.cz> - 1:1.8.0.40-25.b25
- refresh s390 patches

* Fri Mar 27 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-24.b25
- added patch501 1182011_JavaPrintApiDoesNotPrintUmlautCharsWithPostscriptOutputCorrectly.patch
- added patch502 1182694_javaApplicationMenuMisbehave.patch
- both upstreamed, will be gone with u60

* Wed Mar 25 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-23.b25
- Disable various EC algorithms in configuration

* Mon Mar 23 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-22.b25
- sytemtap made working for dual package

* Tue Mar 03 2015 Severin Gehwolf <sgehwolf@redhat.com> - 1:1.8.0.40-21.b25
- Added compiler no-warn-

* Fri Feb 20 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-21.b25
- Fix zero interpreter build.

* Thu Feb 12 2015 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-21.b25
- Fix building with gcc 5 by ignoring return-local-addr warning
- Include additional debugging info for java class files and test that they are
  present

* Thu Feb 12 2015 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-20.b25
- bumped to b25
- removed upstreamed patch11 hotspot-build-j-directive.patch
- policies repacked to stop spamming yum update
- added and used source20 repackReproduciblePolycies.sh
- added mehanism to force priority size

* Fri Jan 09 2015 Dan Horák <dan[at]danny.cz> - 1:1.8.0.40-19.b12
- refresh s390 patches

* Fri Nov 07 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-18.b12
- updated arm64 tarball to jdk8-jdk8u40-b12-aarch64-1263.tar.xz

* Fri Nov 07 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-17.b12
- obsoleted gcj and sindoc. rh1149674 and rh1149675
- removed backup/restore on images and docs in favor of reconfigure in different directory

* Mon Nov 03 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-16.b12
- updated both noral and aarch64 tarballs to u40b12

* Mon Nov 03 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-15.b02
- enabled debug packages
- removed all provides duplicating package name
- comments about files moved inside files section (to prevent different javadoc postuns)
 - see (RH1160693)

* Fri Oct 31 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-13.b02
- Build against libjpeg-turbo-1.4

* Fri Oct 24 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-13.b02
- preparing for parallel debug+normal build
- files and scripelts moved to extendable macros as first step to dual build
- install and build may be done in loop for both release and slowdebug
- debugbuild off untill its completed

* Fri Oct 24 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-12.b02
- added patch12,removeSunEcProvider-RH1154143
- xdump excluded from ppc64le (rh1156151)
- Add check for src.zip completeness. See RH1130490 (by sgehwolf@redhat.com)
- Resolves: rhbz#1125260

* Thu Sep 25 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-11.b02
- fixing flags usages (thanx to jerboaa!)

* Thu Sep 25 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-10.b26
- sync with rhel7

* Wed Sep 17 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.20-9.b26
- Remove LIBDIR and funny definition of _libdir.
- Fix rpmlint warnings about macros in comments.

* Thu Sep 11 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-8.b26
- fixed headless to become headless again
 - jre/bin/policytool added to not headless exclude list

* Wed Sep 10 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.20-7.b26
- Update aarch64 hotspot to latest upstream version

* Fri Sep 05 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.40-6.b26
- Use %%{power64} instead of %%{ppc64}.

* Thu Sep 04 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-5.b26
- Update aarch64 hotspot to jdk7u40-b02 to match the rest of the JDK
- commented out patch2 (obsolated by 666)
- all ppc64 added to jitarches

* Thu Sep 04 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.20-4.b26
- Use the cpp interpreter on ppc64le.

* Wed Sep 03 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-3.b26
- fixed RH1136544, orriginal issue, state of pc64le jit remians mistery

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.20-2.b26
- requirement Requires: javazi-1.8/tzdb.dat changed to tzdata-java >= 2014f-1
- see RH1130800#c5

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-1.b02
- adapted aarch64 patch
- removed upstreamed patch  0001-PPC64LE-arch-support-in-openjdk-1.8.patch

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-1.b02
- updated to u40-b02
- adapted aarch64 patches

* Wed Aug 27 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.40-1.b01
- updated to u40-b01
- adapted  java-1.8.0-openjdk-accessible-toolkit.patch
- adapted  system-lcms.patch
- removed patch8 set-active-window.patch
- removed patch9 javadoc-error-jdk-8029145.patch
- removed patch10 javadoc-error-jdk-8037484.patch
- removed patch99 applet-hole.patch - itw 1.5.1 is able to ive without it

* Tue Aug 19 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-19.b12
- fixed desktop icons
- Icon set to java-1.8.0
- Development removed from policy tool

* Mon Aug 18 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-18.b12
- fixed jstack

* Mon Aug 18 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-17.b12
- added build requires and requires for headles  _datadir/javazi-1.8/tzdb.dat
- restriction of tzdata provider, so we will be aware of another possible failure

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org>
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Aug 14 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-15.b12
- fixed provides/obsolates

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-14.b12
- forced to build in fully versioned dir

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-13.b12
- fixing tapset to support multipleinstalls
- added more config/norepalce
- policitool moved to jre

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-12.b12
- bumped release to build by previous release.
- forcing rebuild by jdk8
- uncommenting forgotten comment on tzdb link

* Tue Aug 12 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-11.b12
- backporting old fixes:
- get rid of jre-abrt, uniquesuffix, parallel install, jsa files,
  config(norepalce) bug, -fstack-protector-strong, OrderWithRequires,
  nss config, multilib arches, provides/requires excludes
- some additional cosmetic changes

* Tue Jul 22 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.11-8.b12
- Modify aarch64-specific jvm.cfg to list server vm first

* Mon Jul 21 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-7.b12
- removed legacy aarch64 switches
 - --with-jvm-variants=client and  --disable-precompiled-headers

* Tue Jul 15 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-6.b12
- added patch patch9999 enableArm64.patch to enable new hotspot

* Tue Jul 15 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-5.b12
- Attempt to update aarch64 *jdk* to u11b12, by resticting aarch64 sources to hotpot only

* Tue Jul 15 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.11-1.b12
- updated to security u11b12

* Tue Jun 24 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-13.b13
- Obsolete java-1.7.0-openjdk

* Wed Jun 18 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-12.b13
- Use system tzdata from tzdata-java

* Thu Jun 12 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-11.b13
- Add patch from IcedTea to handle -j and -I correctly

* Wed Jun 11 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-11.b13
- Backport javadoc fixes from upstream
- Related: rhbz#1107273

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.0.5-10.b13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Jun 02 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-9.b13
- Build with OpenJDK 8

* Wed May 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-8.b13
- Backport fix for JDK-8012224

* Wed May 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-7.b13
- Require fontconfig and minimal fonts (xorg-x11-fonts-Type1) explicitly
- Resolves rhbz#1101394

* Fri May 23 2014 Dan Horák <dan[at]danny.cz> - 1:1.8.0.5-6.b13
- Enable build on s390/s390x

* Tue May 20 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-5.b13
- Only check for debug symbols in libjvm if it exists.

* Fri May 16 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-4.b13
- Include all sources in src.zip

* Mon Apr 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-4.b13
- Check for debug symbols in libjvm.so

* Thu Apr 24 2014 Brent Baude <baude@us.ibm.com> - 1:1.8.0.5-3.b13
- Add ppc64le support, bz# 1088344

* Wed Apr 23 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-2.b13
- Build with -fno-devirtualize
- Don't strip debuginfo from files

* Wed Apr 16 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-1.b13
- Instrument build with various sanitizers.

* Tue Apr 15 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.5-1.b13
- Update to the latest security release: OpenJDK8 u5 b13

* Fri Mar 28 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-2.b132
- Include version information in desktop files
- Move desktop files from tarball to top level source

* Tue Mar 25 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-1.0.b132
- Switch from java8- style provides to java- style
- Bump priority to reflect java version

* Fri Mar 21 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.35.b132
- Disable doclint for compatiblity
- Patch contributed by Andrew John Hughes

* Tue Mar 11 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.34.b132
- Include jdeps and jjs for aarch64. These are present in b128.

* Mon Mar 10 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.33.b132
- Update aarch64 tarball to the latest upstream release

* Fri Mar 07 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.32.b132
- Fix `java -version` output

* Fri Mar 07 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.31.b132
- updated to rc4 aarch64 tarball
- outdated removed: patch2031 system-lcmsAARCH64.patch patch2011 system-libjpeg-aarch64.patch
  patch2021 system-libpng-aarch64.patch

* Thu Mar 06 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.30.b132
- Update to b132

* Thu Mar 06 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.29.b129
- Fix typo in STRIP_POLICY

* Mon Mar 03 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.28.b129
- Remove redundant debuginfo files
- Generate complete debug information for libjvm

* Tue Feb 25 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.27.b129
- Fix non-headless libraries

* Tue Feb 25 2014 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.26.b129
- Fix incorrect Requires

* Thu Feb 13 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.26.b129
- Add -headless subpackage based on java-1.7.0-openjdk
- Add abrt connector support
- Add -accessibility subpackage

* Thu Feb 13 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.26.b129
- Update to b129.

* Fri Feb 07 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.25.b126
- Update to candidate Reference Implementation release.

* Fri Jan 31 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.24.b123
- Forward port more patches from java-1.7.0-openjdk

* Mon Jan 20 2014 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.23.b123
- Update to jdk8-b123

* Thu Nov 14 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.22.b115
- Update to jdk8-b115

* Wed Oct 30 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.21.b106
- added jre/lib/security/blacklisted.certs for aarch64
- updated to preview_rc2 aarch64 tarball

* Sun Oct 06 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.20.b106
- Fix paths in tapsets to work on non-x86_64
- Use system libjpeg

* Thu Sep 05 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.19.b106
- Fix with_systemtap conditionals

* Thu Sep 05 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.18.b106
- Update to jdk8-b106

* Tue Aug 13 2013 Deepak Bhole <dbhole@redhat.com> - 1:1.8.0.0-0.17.b89x
- Updated aarch64 to latest head
- Dropped upstreamed patches

* Wed Aug 07 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.16.b89x
- The zero fix only applies on b89 tarball

* Tue Aug 06 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.16.b89x
- Add patch to fix zero on 32-bit build

* Mon Aug 05 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.16.b89x
- Added additional build fixes for aarch64

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.8.0.0-0.16.b89x
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Aug 02 2013 Deepak Bhole <dbhole@redhat.com> - 1:1.8.0.0-0.15.b89
- Added a missing includes patch (#302/%%{name}-arm64-missing-includes.patch)
- Added --disable-precompiled-headers for arm64 build

* Mon Jul 29 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.14.b89
- added patch 301 - removeMswitchesFromx11.patch

* Fri Jul 26 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.13.b89
- added new aarch64 tarball

* Thu Jul 25 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.12.b89
- ifarchaarch64 then --with-jvm-variants=client

* Tue Jul 23 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.11.b89
- prelink dependence excluded also for aaech64
- arm64 added to jitarches
- added source100 config.guess to repalce the outdated one in-tree
- added source101 config.sub  to repalce the outdated one in-tree
- added patch2011 system-libjpegAARCH64.patch (as aarch64-port is little bit diferent)
- added patch2031 system-lcmsAARCH64.patch (as aarch64-port is little bit diferent)
- added gcc-c++ build depndece so builddep will  result to better situation

* Tue Jul 23 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.10.b89
- moved to latest working osurces

* Tue Jul 23 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.10.b89
- Moved  to hg clone for generating sources.

* Sun Jul 21 2013 Jiri Vanek <jvanek@redhat.com> - 1:1.8.0.0-0.9.b89
- added aarch 64 tarball, proposed usage of clone instead of tarballs

* Mon Jul 15 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.9.b89
- Switch to xz for compression
- Fixes RHBZ#979823

* Mon Jul 15 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.9.b89
- Priority should be 0 until openjdk8 is released by upstream
- Fixes RHBZ#964409

* Mon Jun 3 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.8.b89
- Fix incorrect permissions on ct.sym

* Mon May 20 2013 Omair Majid <omajid@redhat.com> - 1:1.8.0.0-0.7.b89
- Fix incorrect permissions on jars

* Fri May 10 2013 Adam Williamson <awilliam@redhat.com>
- update scriptlets to follow current guidelines for updating icon cache

* Tue Apr 30 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.5.b87
- Update to b87
- Remove all rhino support; use nashorn instead
- Remove upstreamed/unapplied patches

* Tue Apr 23 2013 Karsten Hopp <karsten@redhat.com> 1:1.8.0.0-0.4.b79
- update java-1.8.0-openjdk-ppc-zero-hotspot patch
- use power64 macro

* Thu Mar 28 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.3.b79
- Add build fix for zero
- Drop gstabs fixes; enable full debug info instead

* Wed Mar 13 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.2.b79
- Fix alternatives priority

* Tue Mar 12 2013 Omair Majid <omajid@redhat.com> 1:1.8.0.0-0.1.b79.f19
- Update to jdk8-b79
- Initial version for Fedora 19

* Tue Sep 04 2012 Andrew John Hughes <gnu.andrew@redhat.com> - 1:1.8.0.0-b53.1
- Initial build from java-1.7.0-openjdk RPM
