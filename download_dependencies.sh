if ls osp/core/java/lib/jars/*.jars && ls osp/core/java/lib/so/*.so
  then
    exit 0
fi

mkdir tmp
cd tmp
wget https://bitbucket.org/dtsarkov/factplusplus/downloads/FaCTpp-OWLAPI-4.x-v1.6.5.jar
wget https://bitbucket.org/dtsarkov/factplusplus/downloads/FaCTpp-linux-v1.6.5.zip
sha256sum FaCTpp-OWLAPI-4.x-v1.6.5.jar | grep "c9bc37ec6da3dc591e73b3000086538d43533bf641bf2f38ea163db1089d055a"
CHECK1=$?
sha256sum FaCTpp-linux-v1.6.5.zip | grep "060bda6f156844f6bcdc58fbe52f4595c2e6bdbe1a0fca6a78b221e8c93873e6"
CHECK2=$?
echo $CHECK1
echo $CHECK2
if [[ $CHECK1 != 0 || $CHECK2 != 0 ]]
  then
    echo "Invalid checksum of downloaded files"
    exit 1
fi
unzip *.zip
cd ..

mvn install:install-file -Dfile=tmp/FaCTpp-OWLAPI-4.x-v1.6.5.jar -DgroupId=uk.ac.manchester.cs \
    -DartifactId=factplusplus -Dversion=1.6.5 -Dpackaging=jar
mvn dependency:copy-dependencies -DoutputDirectory=lib/jars -Dhttps.protocols=TLSv1.2 -f osp/core/java/pom.xml
if [[ "$(uname -m)" ==  "x86_64" ]]
  then
    mv -v tmp/FaCT++-linux-v1.6.5/64bit/* osp/core/java/lib/so
  else
    mv -v tmp/FaCT++-linux-v1.6.5/32bit/* osp/core/java/lib/so
fi
rm -rf tmp
exit 0
