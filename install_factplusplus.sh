mvn dependency:copy-dependencies -DoutputDirectory=lib/jars -Dhttps.protocols=TLSv1.2 -f osp/core/java/pom.xml

mkdir tmp
cd tmp
wget https://bitbucket.org/dtsarkov/factplusplus/downloads/FaCTpp-OWLAPI-4.x-v1.6.5.jar
wget https://bitbucket.org/dtsarkov/factplusplus/downloads/FaCTpp-linux-v1.6.5.zip
unzip *.zip
cd ..

mkdir java/osp.core/lib/so
mv tmp/FaCTpp-OWLAPI-4.x-v1.6.5.jar java/osp.core/lib/jars
if [[ "$(uname -m)" ==  "x86_64" ]]
  then
    mv tmp/Fact++-linux-v1.6.5/64bit/* osp/core/java/lib/so
  else
    mv tmp/Fact++-linux-v1.6.5/64bit/* osp/core/java/lib/so
fi
mvn package -f osp/core/java/pom.xml
rm -rf tmp
touch osp/core/java/target/__init__.py
touch osp/core/java/lib/__init__.py
touch osp/core/java/lib/so/__init__.py
touch osp/core/java/lib/jars/__init__.py