window.BENCHMARK_DATA = {
  "lastUpdate": 1649321766561,
  "repoUrl": "https://github.com/simphony/osp-core",
  "entries": {
    "Benchmark": [
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "d2106ce0be96e5f7b94f2262586456a3b3021de5",
          "message": "Updated docker image.",
          "timestamp": "2021-06-02T10:15:43+02:00",
          "tree_id": "965d17ff47257266eb99602e375ae4c5d5e4bb0f",
          "url": "https://github.com/simphony/osp-core/commit/d2106ce0be96e5f7b94f2262586456a3b3021de5"
        },
        "date": 1622621988064,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 128.64625019355034,
            "unit": "iter/sec",
            "range": "stddev: 0.005153894187014561",
            "extra": "mean: 7.773254163999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.14831373591512,
            "unit": "iter/sec",
            "range": "stddev: 0.0033471352705642513",
            "extra": "mean: 7.990519169999967 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 125.99540058124444,
            "unit": "iter/sec",
            "range": "stddev: 0.003266985200362325",
            "extra": "mean: 7.936797655999986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 229.39210617480813,
            "unit": "iter/sec",
            "range": "stddev: 0.0013666526319144117",
            "extra": "mean: 4.359347915999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 279.84483000436353,
            "unit": "iter/sec",
            "range": "stddev: 0.0007831569986133275",
            "extra": "mean: 3.5734088780000235 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 398.57436359217394,
            "unit": "iter/sec",
            "range": "stddev: 0.0001981805401423121",
            "extra": "mean: 2.508942098000091 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.235172734691302,
            "unit": "iter/sec",
            "range": "stddev: 0.006540498050333386",
            "extra": "mean: 89.00619720000024 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 442.1637723533681,
            "unit": "iter/sec",
            "range": "stddev: 0.048502225522917185",
            "extra": "mean: 2.261605456000183 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 693.1218995105404,
            "unit": "iter/sec",
            "range": "stddev: 0.030729945808742637",
            "extra": "mean: 1.4427476620002437 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 361.987804044455,
            "unit": "iter/sec",
            "range": "stddev: 0.0005678897907963088",
            "extra": "mean: 2.7625240100000497 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.99417750773507,
            "unit": "iter/sec",
            "range": "stddev: 0.009461794716881829",
            "extra": "mean: 90.95723616400039 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5061.394615465168,
            "unit": "iter/sec",
            "range": "stddev: 0.00011586069130436673",
            "extra": "mean: 197.57400399970493 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8075.229092632582,
            "unit": "iter/sec",
            "range": "stddev: 0.000019267988146653417",
            "extra": "mean: 123.83549600002651 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 13609.510216949588,
            "unit": "iter/sec",
            "range": "stddev: 0.000029108286446393328",
            "extra": "mean: 73.47802999953501 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9545.987124801051,
            "unit": "iter/sec",
            "range": "stddev: 0.00002482937192593551",
            "extra": "mean: 104.75605999948812 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 213.72642124706607,
            "unit": "iter/sec",
            "range": "stddev: 0.0011346798431396076",
            "extra": "mean: 4.678878699999416 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "37355c322be794f0c298238c1e0195470a9e0e2f",
          "message": "Refresh PR.",
          "timestamp": "2021-06-02T10:50:27+02:00",
          "tree_id": "e5734f5912b8c2a3d9234fb5f0bcbd584a887661",
          "url": "https://github.com/simphony/osp-core/commit/37355c322be794f0c298238c1e0195470a9e0e2f"
        },
        "date": 1622624761898,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 137.52091645694603,
            "unit": "iter/sec",
            "range": "stddev: 0.005581769314782294",
            "extra": "mean: 7.271621115999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 123.52401823813157,
            "unit": "iter/sec",
            "range": "stddev: 0.004145250933284245",
            "extra": "mean: 8.095591564 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 123.04355157588877,
            "unit": "iter/sec",
            "range": "stddev: 0.0040378578065194464",
            "extra": "mean: 8.127203637999969 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 229.2878177351415,
            "unit": "iter/sec",
            "range": "stddev: 0.001265394652891297",
            "extra": "mean: 4.361330705999983 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 283.3410413902518,
            "unit": "iter/sec",
            "range": "stddev: 0.000706917030129746",
            "extra": "mean: 3.529315749999938 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 383.3086426988027,
            "unit": "iter/sec",
            "range": "stddev: 0.00037342727013191365",
            "extra": "mean: 2.6088636899997653 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.108218549267761,
            "unit": "iter/sec",
            "range": "stddev: 0.007871096847269802",
            "extra": "mean: 90.02343585199975 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 463.4807451980934,
            "unit": "iter/sec",
            "range": "stddev: 0.04667162075131904",
            "extra": "mean: 2.1575869340000224 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 710.1243763104693,
            "unit": "iter/sec",
            "range": "stddev: 0.029986353273167784",
            "extra": "mean: 1.4082040179997932 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 386.785367155788,
            "unit": "iter/sec",
            "range": "stddev: 0.000355188074836967",
            "extra": "mean: 2.5854132160000347 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.361945300244368,
            "unit": "iter/sec",
            "range": "stddev: 0.005375414286229803",
            "extra": "mean: 88.013097544 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4809.948589833292,
            "unit": "iter/sec",
            "range": "stddev: 0.00011830085272262114",
            "extra": "mean: 207.90242999970587 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7967.823760357772,
            "unit": "iter/sec",
            "range": "stddev: 0.000024702975113562658",
            "extra": "mean: 125.50478400078191 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16542.697894518165,
            "unit": "iter/sec",
            "range": "stddev: 0.000018249943870623496",
            "extra": "mean: 60.449631999347275 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10555.509662558474,
            "unit": "iter/sec",
            "range": "stddev: 0.000019502428052441993",
            "extra": "mean: 94.73725399988098 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 235.3903848927603,
            "unit": "iter/sec",
            "range": "stddev: 0.0005841984354278254",
            "extra": "mean: 4.248261883999987 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "55ac8a2ebea5d34da5a0205c9debd627a1843484",
          "message": "108 Do continuous benchmarks (#647)\n\n* Benchmark class to control iterations and times.\r\n\r\n* Add benchmarks for all the the methods of the CUDS API referenced in the CUDS API tutorial.\r\n\r\n* Add wrapper functions to make the benchmarks compatible with pytest-benchmark.\r\n\r\n* Add `pytest.ini` file, needed for the benchmarks.\r\n\r\n* Simplify pytest-benchmark wrapper functions using a template.\r\n\r\n* Move pytest-benchmark wrapper functions template to the benchmark class.\r\n\r\n* Change default size of CUDS API benchmarks to 500.\r\n\r\n* Add benchmarks workflow.\r\n\r\n* Update benchmark token name.\r\n\r\n* Enable benchmarks on the PR branch (for testing).\r\n\r\n* Workflow test.\r\n\r\n* Updated docker image.\r\n\r\n* Remove PR branch from `benchmarks.yml`.",
          "timestamp": "2021-06-16T14:22:22+02:00",
          "tree_id": "7e3d2f2b466bd504586e8606a4b602bb9f081a85",
          "url": "https://github.com/simphony/osp-core/commit/55ac8a2ebea5d34da5a0205c9debd627a1843484"
        },
        "date": 1623846356272,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 154.75321840848648,
            "unit": "iter/sec",
            "range": "stddev: 0.005293061680850901",
            "extra": "mean: 6.46190115 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 113.0983054397646,
            "unit": "iter/sec",
            "range": "stddev: 0.004972992426035721",
            "extra": "mean: 8.841865456000075 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 126.79217236169214,
            "unit": "iter/sec",
            "range": "stddev: 0.00360839318592621",
            "extra": "mean: 7.88692220800005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 212.81248867105896,
            "unit": "iter/sec",
            "range": "stddev: 0.001809650646226487",
            "extra": "mean: 4.698972350000027 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 238.5130374076588,
            "unit": "iter/sec",
            "range": "stddev: 0.0013954273975939077",
            "extra": "mean: 4.192642929999806 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 342.6443351931054,
            "unit": "iter/sec",
            "range": "stddev: 0.0007187620509322808",
            "extra": "mean: 2.9184781339998693 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.117580189426876,
            "unit": "iter/sec",
            "range": "stddev: 0.01526685733525202",
            "extra": "mean: 98.83786253999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 438.62527158673873,
            "unit": "iter/sec",
            "range": "stddev: 0.049452262083969106",
            "extra": "mean: 2.2798503980002636 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 694.9592393620153,
            "unit": "iter/sec",
            "range": "stddev: 0.03070969937628243",
            "extra": "mean: 1.4389333119997332 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 320.3229694008756,
            "unit": "iter/sec",
            "range": "stddev: 0.0010907275415568498",
            "extra": "mean: 3.1218491820002043 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.685197728012053,
            "unit": "iter/sec",
            "range": "stddev: 0.010863163681414014",
            "extra": "mean: 93.58741180600003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4912.253979125075,
            "unit": "iter/sec",
            "range": "stddev: 0.00010779581531485208",
            "extra": "mean: 203.57253599866 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7771.803678613777,
            "unit": "iter/sec",
            "range": "stddev: 0.000029377711838124",
            "extra": "mean: 128.6702600004901 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16434.71909330291,
            "unit": "iter/sec",
            "range": "stddev: 0.000020537605534430002",
            "extra": "mean: 60.84679600076015 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10255.972878643723,
            "unit": "iter/sec",
            "range": "stddev: 0.000029133519963881722",
            "extra": "mean: 97.50415799970824 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 278.46983937675896,
            "unit": "iter/sec",
            "range": "stddev: 0.0006279353429754167",
            "extra": "mean: 3.5910531719991354 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "415c676be9f39acd4cc0a730c0469eb43aa9ea46",
          "message": "Decouple the parsers actions (#658)\n\n* Decouple the following operations that the parser was responsible for: get the graph of the ontology, put the ontology in the namespace registry.\r\n\r\n* Modify the unit tests to accommodate the new changes.\r\n\r\n* Make the `Ontology` class directly accesible from the `ontology` module.",
          "timestamp": "2021-06-16T14:55:54+02:00",
          "tree_id": "4e1bf85a2b9adddb0fbdb4e492eeec141d7fc92b",
          "url": "https://github.com/simphony/osp-core/commit/415c676be9f39acd4cc0a730c0469eb43aa9ea46"
        },
        "date": 1623848364523,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 149.699370326335,
            "unit": "iter/sec",
            "range": "stddev: 0.005340880188970438",
            "extra": "mean: 6.680054817999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.16502749157353,
            "unit": "iter/sec",
            "range": "stddev: 0.0037679208134168613",
            "extra": "mean: 7.989452165999987 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 110.04512566986385,
            "unit": "iter/sec",
            "range": "stddev: 0.0048086565032759414",
            "extra": "mean: 9.087181226000023 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 211.7488964108043,
            "unit": "iter/sec",
            "range": "stddev: 0.0017136593041086855",
            "extra": "mean: 4.722574790000067 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 272.46423253714215,
            "unit": "iter/sec",
            "range": "stddev: 0.0007754128884990152",
            "extra": "mean: 3.6702065100000993 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 351.78020066123213,
            "unit": "iter/sec",
            "range": "stddev: 0.0006565806622675701",
            "extra": "mean: 2.84268414800016 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.607426830453921,
            "unit": "iter/sec",
            "range": "stddev: 0.011742099968498598",
            "extra": "mean: 94.2735703939998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 447.90213385678857,
            "unit": "iter/sec",
            "range": "stddev: 0.04843202629358056",
            "extra": "mean: 2.2326305779997426 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 694.1601665739413,
            "unit": "iter/sec",
            "range": "stddev: 0.030603949161829867",
            "extra": "mean: 1.4405897200001334 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 370.82607798826155,
            "unit": "iter/sec",
            "range": "stddev: 0.00044350905890792376",
            "extra": "mean: 2.69668197399983 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.450468440786846,
            "unit": "iter/sec",
            "range": "stddev: 0.01146252064645033",
            "extra": "mean: 95.68949044400034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4725.189990679727,
            "unit": "iter/sec",
            "range": "stddev: 0.00011480310406396242",
            "extra": "mean: 211.6317019998064 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 6218.08312338896,
            "unit": "iter/sec",
            "range": "stddev: 0.00006411367610048244",
            "extra": "mean: 160.82126600053925 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14366.097939689265,
            "unit": "iter/sec",
            "range": "stddev: 0.00003256666373039656",
            "extra": "mean: 69.60832399988703 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10291.675553544215,
            "unit": "iter/sec",
            "range": "stddev: 0.0000193231156871017",
            "extra": "mean: 97.1659079998517 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 265.1533479838543,
            "unit": "iter/sec",
            "range": "stddev: 0.0008989535873424225",
            "extra": "mean: 3.7714025020000577 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "6ad48a46f529801b4c08a5859fecc131bd5881f8",
          "message": "638 Strange behaviour of CUDS remove (#659)\n\n* Do not put the wrapper in the added buffer.\r\n\r\n* Have the assumption \"the wrapper is not put in the added buffer\" baked in the transport session.\r\n\r\n* Have the assumption \"the wrapper is not put in the added buffer\" also baked in the unit tests. Notice how when `wrapper.add` is used, the wrapper is expected in the updated buffer instead of the added buffer. When `wrapper.add` is not used, the wrapper is not expected in neither buffer.",
          "timestamp": "2021-06-24T16:42:27+02:00",
          "tree_id": "154f06bf56025d67c76ec06cf06d22c37b5b16ca",
          "url": "https://github.com/simphony/osp-core/commit/6ad48a46f529801b4c08a5859fecc131bd5881f8"
        },
        "date": 1624545953487,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 153.42967093996137,
            "unit": "iter/sec",
            "range": "stddev: 0.00585484876538198",
            "extra": "mean: 6.517644168000011 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 123.03862309945542,
            "unit": "iter/sec",
            "range": "stddev: 0.0037557416770005753",
            "extra": "mean: 8.127529183999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 119.9018405261524,
            "unit": "iter/sec",
            "range": "stddev: 0.004146395614108172",
            "extra": "mean: 8.340155544000051 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 191.16128382502197,
            "unit": "iter/sec",
            "range": "stddev: 0.0021221515316505635",
            "extra": "mean: 5.231184787999972 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 280.7271379504795,
            "unit": "iter/sec",
            "range": "stddev: 0.0009097018556484361",
            "extra": "mean: 3.562177876000007 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 397.4081839418095,
            "unit": "iter/sec",
            "range": "stddev: 0.00021381069121657623",
            "extra": "mean: 2.5163044960000747 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.801280157519294,
            "unit": "iter/sec",
            "range": "stddev: 0.00845714261988745",
            "extra": "mean: 92.58161860599937 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 435.16815367884885,
            "unit": "iter/sec",
            "range": "stddev: 0.04986877000153655",
            "extra": "mean: 2.297962273999474 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 700.7014868328368,
            "unit": "iter/sec",
            "range": "stddev: 0.030408382874563912",
            "extra": "mean: 1.4271412560004535 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 375.9768262381991,
            "unit": "iter/sec",
            "range": "stddev: 0.0005049011042808997",
            "extra": "mean: 2.6597383939999872 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.096825608225522,
            "unit": "iter/sec",
            "range": "stddev: 0.00770153903936455",
            "extra": "mean: 90.11586153600089 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 3998.3989770713697,
            "unit": "iter/sec",
            "range": "stddev: 0.00015901798829669417",
            "extra": "mean: 250.1001040002393 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7292.422222379798,
            "unit": "iter/sec",
            "range": "stddev: 0.000027887446410848072",
            "extra": "mean: 137.1286479999867 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16366.120324206779,
            "unit": "iter/sec",
            "range": "stddev: 0.000016454528321624603",
            "extra": "mean: 61.101835999636485 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10113.19230947822,
            "unit": "iter/sec",
            "range": "stddev: 0.000020664822733354925",
            "extra": "mean: 98.88074599973606 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 285.1159831832923,
            "unit": "iter/sec",
            "range": "stddev: 0.00030982515672498575",
            "extra": "mean: 3.5073445860000447 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "c2d110555cd1d416f03153c96b92d13f705f258d",
          "message": "622 Update license file (#661)\n\nMove partners to README.",
          "timestamp": "2021-06-30T09:04:05+02:00",
          "tree_id": "5acc09f87e7e84275c9a9e396fffd2a356926923",
          "url": "https://github.com/simphony/osp-core/commit/c2d110555cd1d416f03153c96b92d13f705f258d"
        },
        "date": 1625036839064,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 163.6637880333977,
            "unit": "iter/sec",
            "range": "stddev: 0.0053187673527700235",
            "extra": "mean: 6.1100871000000145 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.1535005494054,
            "unit": "iter/sec",
            "range": "stddev: 0.00359488591665041",
            "extra": "mean: 7.9901880139999895 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 124.49888529487416,
            "unit": "iter/sec",
            "range": "stddev: 0.0038444018903876667",
            "extra": "mean: 8.032200429999929 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 219.80897137339886,
            "unit": "iter/sec",
            "range": "stddev: 0.0015764276232287267",
            "extra": "mean: 4.5494048479998455 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 267.31789411676607,
            "unit": "iter/sec",
            "range": "stddev: 0.0009166893366184737",
            "extra": "mean: 3.740864423999966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 342.91542664417716,
            "unit": "iter/sec",
            "range": "stddev: 0.000815863855519592",
            "extra": "mean: 2.916170934000121 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.929860393154888,
            "unit": "iter/sec",
            "range": "stddev: 0.008030364126910114",
            "extra": "mean: 91.49247694199975 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 457.93165053416226,
            "unit": "iter/sec",
            "range": "stddev: 0.04729021841225897",
            "extra": "mean: 2.183732001999715 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 636.0660165641668,
            "unit": "iter/sec",
            "range": "stddev: 0.03336756085896143",
            "extra": "mean: 1.572163854000081 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 376.9737846933997,
            "unit": "iter/sec",
            "range": "stddev: 0.0003339699468602238",
            "extra": "mean: 2.6527043539998942 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.928145313227525,
            "unit": "iter/sec",
            "range": "stddev: 0.007264247662305863",
            "extra": "mean: 91.50683591199973 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5099.712953461493,
            "unit": "iter/sec",
            "range": "stddev: 0.00011079633577239684",
            "extra": "mean: 196.08946800059357 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7923.033748680502,
            "unit": "iter/sec",
            "range": "stddev: 0.00002235504535403208",
            "extra": "mean: 126.21427999931711 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 17081.613215007033,
            "unit": "iter/sec",
            "range": "stddev: 0.000015052348003699116",
            "extra": "mean: 58.542479999573516 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9348.824809775188,
            "unit": "iter/sec",
            "range": "stddev: 0.000038135617707671404",
            "extra": "mean: 106.96531599933223 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 252.39129559017255,
            "unit": "iter/sec",
            "range": "stddev: 0.00118160121963872",
            "extra": "mean: 3.962101774000075 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "b0386e2b1a8159887a1260535ce4f16b927615ee",
          "message": "665 Raise a warning instead of an error when the default relationship of an ontology does not belong to the ontology itself. (#666)",
          "timestamp": "2021-07-05T17:04:08+02:00",
          "tree_id": "887b992157ad5c79cfd1d56cc0c27a2962c31fe1",
          "url": "https://github.com/simphony/osp-core/commit/b0386e2b1a8159887a1260535ce4f16b927615ee"
        },
        "date": 1625497646700,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 158.18894263214082,
            "unit": "iter/sec",
            "range": "stddev: 0.005919205639568304",
            "extra": "mean: 6.321554360000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.09148703504852,
            "unit": "iter/sec",
            "range": "stddev: 0.0035351455615890994",
            "extra": "mean: 7.994149112000059 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 118.09425336281993,
            "unit": "iter/sec",
            "range": "stddev: 0.004478495921309633",
            "extra": "mean: 8.467812543999994 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 194.0114568964794,
            "unit": "iter/sec",
            "range": "stddev: 0.0017433982194765643",
            "extra": "mean: 5.154334780000028 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 188.76355456579367,
            "unit": "iter/sec",
            "range": "stddev: 0.0019051628874344197",
            "extra": "mean: 5.297632810000138 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 346.93955298049565,
            "unit": "iter/sec",
            "range": "stddev: 0.0007411301897974653",
            "extra": "mean: 2.8823464820000453 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.554712626511307,
            "unit": "iter/sec",
            "range": "stddev: 0.009999292065161378",
            "extra": "mean: 94.74440805599973 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 415.0970804851223,
            "unit": "iter/sec",
            "range": "stddev: 0.051937710220105314",
            "extra": "mean: 2.4090750020002645 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 671.2886348105852,
            "unit": "iter/sec",
            "range": "stddev: 0.03174491770690052",
            "extra": "mean: 1.489672174000333 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 377.65141524497,
            "unit": "iter/sec",
            "range": "stddev: 0.0002675663687070008",
            "extra": "mean: 2.6479445320000536 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.231547862168853,
            "unit": "iter/sec",
            "range": "stddev: 0.003396944718138928",
            "extra": "mean: 89.03492308199952 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4859.73379507872,
            "unit": "iter/sec",
            "range": "stddev: 0.00011385010053399216",
            "extra": "mean: 205.7725879990926 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7706.267774254743,
            "unit": "iter/sec",
            "range": "stddev: 0.00002624242043807123",
            "extra": "mean: 129.76450199937517 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16512.963452611904,
            "unit": "iter/sec",
            "range": "stddev: 0.000016446173085670675",
            "extra": "mean: 60.558481999294145 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10478.016105910869,
            "unit": "iter/sec",
            "range": "stddev: 0.000017632327867855092",
            "extra": "mean: 95.43791399937618 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 275.429167710993,
            "unit": "iter/sec",
            "range": "stddev: 0.0008668556544457871",
            "extra": "mean: 3.6306975340000918 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "46421269+MBueschelberger@users.noreply.github.com",
            "name": "MBueschelberger",
            "username": "MBueschelberger"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "ea9ce17d588ce57ce017ae33689b8dd207b44172",
          "message": "Fetch datatypes from Sparql-Result (#663)\n\nCloses #655. Makes SparqlResult callable, as in `result(specimen='cuds', cycles=float)`, so that for example `next(result(specimen='cuds', cycles=float))['specimen']` returns a CUDS object instead of an rdflib URIRef.\r\n\r\nCo-authored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>",
          "timestamp": "2021-07-07T17:25:19+02:00",
          "tree_id": "7981ad62a9e2fd62b588168170cfb63763d95153",
          "url": "https://github.com/simphony/osp-core/commit/ea9ce17d588ce57ce017ae33689b8dd207b44172"
        },
        "date": 1625671713022,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 156.84849336416025,
            "unit": "iter/sec",
            "range": "stddev: 0.005071514817528836",
            "extra": "mean: 6.375579252000001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 121.88287226465093,
            "unit": "iter/sec",
            "range": "stddev: 0.004577347912139084",
            "extra": "mean: 8.204598246000025 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 126.29119026826135,
            "unit": "iter/sec",
            "range": "stddev: 0.003948388620953865",
            "extra": "mean: 7.918208687999936 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 220.89414448071759,
            "unit": "iter/sec",
            "range": "stddev: 0.001483439698932049",
            "extra": "mean: 4.527055266000012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 276.10540732559815,
            "unit": "iter/sec",
            "range": "stddev: 0.0007526696270558311",
            "extra": "mean: 3.621805200000111 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 388.06854389493134,
            "unit": "iter/sec",
            "range": "stddev: 0.0002821336864100692",
            "extra": "mean: 2.576864360000144 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.072815535962313,
            "unit": "iter/sec",
            "range": "stddev: 0.0068930848915675245",
            "extra": "mean: 90.31126697199984 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 479.3349031116214,
            "unit": "iter/sec",
            "range": "stddev: 0.045131895237755945",
            "extra": "mean: 2.086224044000261 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 705.9631838984319,
            "unit": "iter/sec",
            "range": "stddev: 0.030151727115392078",
            "extra": "mean: 1.416504462000205 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 358.7565945309776,
            "unit": "iter/sec",
            "range": "stddev: 0.0006410500183927101",
            "extra": "mean: 2.787405208000024 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.944394980876831,
            "unit": "iter/sec",
            "range": "stddev: 0.007957629194357174",
            "extra": "mean: 91.37097132799963 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4631.920886496501,
            "unit": "iter/sec",
            "range": "stddev: 0.00011867847168072168",
            "extra": "mean: 215.89315199992143 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7905.783926800219,
            "unit": "iter/sec",
            "range": "stddev: 0.000022826402891281993",
            "extra": "mean: 126.48967000097855 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15911.061493770649,
            "unit": "iter/sec",
            "range": "stddev: 0.00001977715373329665",
            "extra": "mean: 62.84935800113089 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10559.596079452198,
            "unit": "iter/sec",
            "range": "stddev: 0.00001885439011341449",
            "extra": "mean: 94.7005919995263 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 283.314176233105,
            "unit": "iter/sec",
            "range": "stddev: 0.00038962972769273886",
            "extra": "mean: 3.529650416000436 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "6eb231ef61c9de50c094b9fd7ad4daed8bec91c7",
          "message": "662 Strange behaviour of CUDS remove (DataspaceSession) (#668)\n\nAllow the CUDS objects to be initialized with extra triples, instead of having to add them after already having created the object.\r\n\r\nThis solves #668 because previously, the class of the `Wrapper` CUDS objects was not defined on the server until after having spawned the CUDS object, because it is created empty and then filled with triples. This caused it to go to the added buffer, ignoring the changes introduced in #638, which solved the issue for local sessions, for which the CUDS objects are not created first empty and then filled with triples.",
          "timestamp": "2021-07-15T14:58:04+02:00",
          "tree_id": "1c4198451ddd9d450ec5a1e2cc9d7c7f3b3d3946",
          "url": "https://github.com/simphony/osp-core/commit/6eb231ef61c9de50c094b9fd7ad4daed8bec91c7"
        },
        "date": 1626354074505,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 152.74569695545281,
            "unit": "iter/sec",
            "range": "stddev: 0.00521975919250445",
            "extra": "mean: 6.546829272000001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 120.86411638535168,
            "unit": "iter/sec",
            "range": "stddev: 0.003698239908356882",
            "extra": "mean: 8.273754278000055 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 130.3488595534917,
            "unit": "iter/sec",
            "range": "stddev: 0.0034935096084990802",
            "extra": "mean: 7.671720361999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 220.2021016474438,
            "unit": "iter/sec",
            "range": "stddev: 0.0014887780620558655",
            "extra": "mean: 4.5412827239998705 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 281.7731038953337,
            "unit": "iter/sec",
            "range": "stddev: 0.0008026803073201144",
            "extra": "mean: 3.5489547660001506 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 374.1490672576385,
            "unit": "iter/sec",
            "range": "stddev: 0.00048530942532117353",
            "extra": "mean: 2.672731505999991 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.181844808289318,
            "unit": "iter/sec",
            "range": "stddev: 0.007394761622979929",
            "extra": "mean: 89.43068135399989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 305.637595851815,
            "unit": "iter/sec",
            "range": "stddev: 0.07126502080951806",
            "extra": "mean: 3.271848795999688 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 696.0941246781791,
            "unit": "iter/sec",
            "range": "stddev: 0.03066398286326945",
            "extra": "mean: 1.4365873299998384 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 377.0951608884476,
            "unit": "iter/sec",
            "range": "stddev: 0.0004459884140597834",
            "extra": "mean: 2.651850524000281 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.102575243029392,
            "unit": "iter/sec",
            "range": "stddev: 0.006905213809008388",
            "extra": "mean: 90.06919368799927 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4885.948429571923,
            "unit": "iter/sec",
            "range": "stddev: 0.00011967020477803859",
            "extra": "mean: 204.66855400019313 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7789.782923882269,
            "unit": "iter/sec",
            "range": "stddev: 0.000023759625923353347",
            "extra": "mean: 128.3732819991883 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16065.908784126033,
            "unit": "iter/sec",
            "range": "stddev: 0.00002058089102349749",
            "extra": "mean: 62.24360000027218 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9492.109494171611,
            "unit": "iter/sec",
            "range": "stddev: 0.00002353572516163188",
            "extra": "mean: 105.35065999965809 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 278.44003905742096,
            "unit": "iter/sec",
            "range": "stddev: 0.0004300808503080159",
            "extra": "mean: 3.591437508000695 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "62147380+yoavnash@users.noreply.github.com",
            "name": "nash",
            "username": "yoavnash"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3c165f73d678eeacedd0ed041672ab31b4a9d287",
          "message": "Merge pull request #671 from simphony/670-Error_when_installing_ontologies\n\n670 Error when installing ontologies",
          "timestamp": "2021-07-15T16:03:14+02:00",
          "tree_id": "46d9b69a428f710b9de909b34a87973869dd6907",
          "url": "https://github.com/simphony/osp-core/commit/3c165f73d678eeacedd0ed041672ab31b4a9d287"
        },
        "date": 1626357987932,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 162.5683568117639,
            "unit": "iter/sec",
            "range": "stddev: 0.004957349179862163",
            "extra": "mean: 6.151258581999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 130.08136609481758,
            "unit": "iter/sec",
            "range": "stddev: 0.003464523641155606",
            "extra": "mean: 7.687496142000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 128.35850002479063,
            "unit": "iter/sec",
            "range": "stddev: 0.0037438684762916823",
            "extra": "mean: 7.7906800079999705 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 226.1658246433117,
            "unit": "iter/sec",
            "range": "stddev: 0.0013723848495728384",
            "extra": "mean: 4.421534515999973 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 271.8477738066104,
            "unit": "iter/sec",
            "range": "stddev: 0.000760541865451263",
            "extra": "mean: 3.6785292960000078 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 386.6089733394814,
            "unit": "iter/sec",
            "range": "stddev: 0.00012459215058924913",
            "extra": "mean: 2.586592834000001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.83120109557604,
            "unit": "iter/sec",
            "range": "stddev: 0.010262838511000585",
            "extra": "mean: 92.32586406399987 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 463.9420619948249,
            "unit": "iter/sec",
            "range": "stddev: 0.04668834154613376",
            "extra": "mean: 2.1554415560000564 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 664.344277629031,
            "unit": "iter/sec",
            "range": "stddev: 0.03206498163677857",
            "extra": "mean: 1.5052436419997264 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 375.74924587500107,
            "unit": "iter/sec",
            "range": "stddev: 0.0005309880196445563",
            "extra": "mean: 2.6613493200001415 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.813410023748625,
            "unit": "iter/sec",
            "range": "stddev: 0.008700777938797208",
            "extra": "mean: 92.47776582999998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5038.60904724687,
            "unit": "iter/sec",
            "range": "stddev: 0.00011042719162299997",
            "extra": "mean: 198.46747199932224 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7422.145479212839,
            "unit": "iter/sec",
            "range": "stddev: 0.00003167187990054204",
            "extra": "mean: 134.73193200007927 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14317.800066591708,
            "unit": "iter/sec",
            "range": "stddev: 0.000033797668601327476",
            "extra": "mean: 69.84313199995995 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9977.79820164692,
            "unit": "iter/sec",
            "range": "stddev: 0.000021918134310753623",
            "extra": "mean: 100.22251200018673 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 285.26366887827487,
            "unit": "iter/sec",
            "range": "stddev: 0.0003895028259267339",
            "extra": "mean: 3.505528775999551 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "13626de492eb65e94084a1b867b8df42d4f1e697",
          "message": "649 Name change of files at the client side – prepended with a hash (#664)\n\n* Do not prepend the CUDS uid to files received from the transport session. Only append the CUDS uid when there is a filename conflict.\r\n\r\n* Adjust tests to the new behaviour for filenames.",
          "timestamp": "2021-07-16T08:37:25+02:00",
          "tree_id": "1da556fabcc1a18886f536991b20ab5e14594c91",
          "url": "https://github.com/simphony/osp-core/commit/13626de492eb65e94084a1b867b8df42d4f1e697"
        },
        "date": 1626417636923,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 153.48988215218458,
            "unit": "iter/sec",
            "range": "stddev: 0.0054868273707691425",
            "extra": "mean: 6.515087417999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 123.11838656135907,
            "unit": "iter/sec",
            "range": "stddev: 0.0037209376681951395",
            "extra": "mean: 8.122263683999996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 113.550646653253,
            "unit": "iter/sec",
            "range": "stddev: 0.00466101060393588",
            "extra": "mean: 8.806642933999989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 216.5092265554157,
            "unit": "iter/sec",
            "range": "stddev: 0.0013222443970320747",
            "extra": "mean: 4.618740807999927 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 278.99677155704586,
            "unit": "iter/sec",
            "range": "stddev: 0.0007683677195800242",
            "extra": "mean: 3.5842708660000824 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 361.5652534403093,
            "unit": "iter/sec",
            "range": "stddev: 0.0005697096907479363",
            "extra": "mean: 2.7657524899999544 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.041699733212553,
            "unit": "iter/sec",
            "range": "stddev: 0.006807932825036957",
            "extra": "mean: 90.56576651800081 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 453.2261765970517,
            "unit": "iter/sec",
            "range": "stddev: 0.04782028900412806",
            "extra": "mean: 2.206403891999969 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 643.7158939766905,
            "unit": "iter/sec",
            "range": "stddev: 0.032926777980397746",
            "extra": "mean: 1.5534803619999025 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 385.650347630262,
            "unit": "iter/sec",
            "range": "stddev: 0.0002181487944718469",
            "extra": "mean: 2.59302242600009 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.750452425189668,
            "unit": "iter/sec",
            "range": "stddev: 0.0094252328828375",
            "extra": "mean: 93.01934099600066 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4588.110163961093,
            "unit": "iter/sec",
            "range": "stddev: 0.00012566949161413023",
            "extra": "mean: 217.954661998931 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7588.713579463814,
            "unit": "iter/sec",
            "range": "stddev: 0.000029559312451473114",
            "extra": "mean: 131.77464000040118 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14600.281948905897,
            "unit": "iter/sec",
            "range": "stddev: 0.00002280294677336343",
            "extra": "mean: 68.4918280002762 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9964.283821748151,
            "unit": "iter/sec",
            "range": "stddev: 0.00002606216416436846",
            "extra": "mean: 100.35844200035626 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 269.03797411434044,
            "unit": "iter/sec",
            "range": "stddev: 0.0007903614418217648",
            "extra": "mean: 3.71694740600077 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "118f08a0b8937a52bec186a62ff83679a5b43b60",
          "message": "652 cuba.file in dataspace session shows wrong file path on second load (#667)\n\n* Transport session: set `cuds.path` for CUDS of type `cuba.File` even when the file which the CUDS references is not moved.\r\n\r\n* Add tests for issue #652.",
          "timestamp": "2021-07-16T09:02:02+02:00",
          "tree_id": "c3c52e3442efdfbba502c5bc765cce6b826dedb7",
          "url": "https://github.com/simphony/osp-core/commit/118f08a0b8937a52bec186a62ff83679a5b43b60"
        },
        "date": 1626419116801,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 162.33921410026073,
            "unit": "iter/sec",
            "range": "stddev: 0.005509330778809066",
            "extra": "mean: 6.159941117999991 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.54342690105373,
            "unit": "iter/sec",
            "range": "stddev: 0.003651905026838891",
            "extra": "mean: 7.965371223999993 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 117.86515573117128,
            "unit": "iter/sec",
            "range": "stddev: 0.004247257285525154",
            "extra": "mean: 8.48427165599998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 210.19754647082428,
            "unit": "iter/sec",
            "range": "stddev: 0.0014685602510897324",
            "extra": "mean: 4.757429459999912 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 251.87967207731455,
            "unit": "iter/sec",
            "range": "stddev: 0.0011820467971340057",
            "extra": "mean: 3.970149681999942 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 389.81324254931167,
            "unit": "iter/sec",
            "range": "stddev: 0.00015314521835198635",
            "extra": "mean: 2.5653310119999304 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.091219191633371,
            "unit": "iter/sec",
            "range": "stddev: 0.006489555208925544",
            "extra": "mean: 90.16141352200009 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 459.70527261563564,
            "unit": "iter/sec",
            "range": "stddev: 0.04694137339673279",
            "extra": "mean: 2.1753067879996024 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 696.1411986980119,
            "unit": "iter/sec",
            "range": "stddev: 0.030523233180933775",
            "extra": "mean: 1.436490186000043 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 383.1771183956797,
            "unit": "iter/sec",
            "range": "stddev: 0.00044223775035675785",
            "extra": "mean: 2.6097591739999757 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.81054120362656,
            "unit": "iter/sec",
            "range": "stddev: 0.013251270022467766",
            "extra": "mean: 92.50230688400086 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4715.961816976391,
            "unit": "iter/sec",
            "range": "stddev: 0.00010731813661303256",
            "extra": "mean: 212.045821999709 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7510.941789823366,
            "unit": "iter/sec",
            "range": "stddev: 0.000027404047556753315",
            "extra": "mean: 133.13909599924045 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16261.732718251087,
            "unit": "iter/sec",
            "range": "stddev: 0.00001556795461030675",
            "extra": "mean: 61.49406199978102 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 8931.453417155286,
            "unit": "iter/sec",
            "range": "stddev: 0.00004026639131158392",
            "extra": "mean: 111.96386000057146 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 281.27892072944735,
            "unit": "iter/sec",
            "range": "stddev: 0.00041209552109768466",
            "extra": "mean: 3.555189978000044 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "4306657f3a5b3e1748dedd59743825de3ca9489a",
          "message": "xsd:double support, enforce rdflib >= 5.0.0. (#672)\n\n* Support xsd:double RDF datatype.\r\n\r\n* Enforce rdflib >= 5.0.0.",
          "timestamp": "2021-07-16T09:15:59+02:00",
          "tree_id": "0b50f1ea73fea5c9bb8da1540baf5eff2522afe9",
          "url": "https://github.com/simphony/osp-core/commit/4306657f3a5b3e1748dedd59743825de3ca9489a"
        },
        "date": 1626419952983,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 160.2438787228523,
            "unit": "iter/sec",
            "range": "stddev: 0.005292744541421917",
            "extra": "mean: 6.240487985999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.08575776356578,
            "unit": "iter/sec",
            "range": "stddev: 0.004260001507049641",
            "extra": "mean: 7.994515265999964 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 121.68474970636873,
            "unit": "iter/sec",
            "range": "stddev: 0.00433726791899278",
            "extra": "mean: 8.217956666000045 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 227.3914047073184,
            "unit": "iter/sec",
            "range": "stddev: 0.001258817631907385",
            "extra": "mean: 4.397703604000014 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 268.4422917348306,
            "unit": "iter/sec",
            "range": "stddev: 0.0009895036640985742",
            "extra": "mean: 3.7251954360001065 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 387.2676115788574,
            "unit": "iter/sec",
            "range": "stddev: 0.0002814292585756592",
            "extra": "mean: 2.5821937339998158 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.008266456354226,
            "unit": "iter/sec",
            "range": "stddev: 0.008079679367988596",
            "extra": "mean: 90.84082438999982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 406.7120853765672,
            "unit": "iter/sec",
            "range": "stddev: 0.05263475395607304",
            "extra": "mean: 2.458741788000026 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 649.6688647540776,
            "unit": "iter/sec",
            "range": "stddev: 0.03295665650667457",
            "extra": "mean: 1.5392456900001434 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 381.47676312539454,
            "unit": "iter/sec",
            "range": "stddev: 0.000428125651392429",
            "extra": "mean: 2.621391645999921 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.064102442669482,
            "unit": "iter/sec",
            "range": "stddev: 0.008488986927705435",
            "extra": "mean: 90.38238801400016 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4403.502711626847,
            "unit": "iter/sec",
            "range": "stddev: 0.00013308298502061311",
            "extra": "mean: 227.09194600008686 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7372.799921476937,
            "unit": "iter/sec",
            "range": "stddev: 0.00004051810200888004",
            "extra": "mean: 135.63368200010473 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16153.097246366733,
            "unit": "iter/sec",
            "range": "stddev: 0.000017989216370314206",
            "extra": "mean: 61.90763200072525 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10500.790909078432,
            "unit": "iter/sec",
            "range": "stddev: 0.00001897743982117862",
            "extra": "mean: 95.23092199992789 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 278.06534043983714,
            "unit": "iter/sec",
            "range": "stddev: 0.0008244805268324559",
            "extra": "mean: 3.596277042001077 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3c39b2991ac78c972e92d1b1f2cddf256f26a9b4",
          "message": "Bump package version to 3.5.4 (#673)",
          "timestamp": "2021-07-16T09:32:45+02:00",
          "tree_id": "45a6fd99afdb0d8abcfff697529960ca63d0b56d",
          "url": "https://github.com/simphony/osp-core/commit/3c39b2991ac78c972e92d1b1f2cddf256f26a9b4"
        },
        "date": 1626420952193,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 151.11869464213189,
            "unit": "iter/sec",
            "range": "stddev: 0.005450376118842454",
            "extra": "mean: 6.617314967999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 122.84885433760289,
            "unit": "iter/sec",
            "range": "stddev: 0.004116303172412003",
            "extra": "mean: 8.140084052000063 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 123.59225040362689,
            "unit": "iter/sec",
            "range": "stddev: 0.0037404346577319465",
            "extra": "mean: 8.091122191999947 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 223.64927386714933,
            "unit": "iter/sec",
            "range": "stddev: 0.0012784205531511609",
            "extra": "mean: 4.471286593999913 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 275.3590921987065,
            "unit": "iter/sec",
            "range": "stddev: 0.0008376837193723415",
            "extra": "mean: 3.6316215019999163 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 383.95133664377545,
            "unit": "iter/sec",
            "range": "stddev: 0.0002917564626098997",
            "extra": "mean: 2.604496728000157 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.498430496018909,
            "unit": "iter/sec",
            "range": "stddev: 0.003695665993463327",
            "extra": "mean: 86.96839106400036 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 441.94260578165944,
            "unit": "iter/sec",
            "range": "stddev: 0.049142782331735024",
            "extra": "mean: 2.262737258000527 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 686.7588687146332,
            "unit": "iter/sec",
            "range": "stddev: 0.030986490573097027",
            "extra": "mean: 1.4561151600002518 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 374.280607968956,
            "unit": "iter/sec",
            "range": "stddev: 0.00040841185789279523",
            "extra": "mean: 2.6717921760000536 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.356012529659454,
            "unit": "iter/sec",
            "range": "stddev: 0.005783626072067402",
            "extra": "mean: 88.05907860599976 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5086.875646158473,
            "unit": "iter/sec",
            "range": "stddev: 0.00010046185312027355",
            "extra": "mean: 196.5843220003194 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7876.928226711322,
            "unit": "iter/sec",
            "range": "stddev: 0.000022142894621005026",
            "extra": "mean: 126.95304200042301 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16768.623249537606,
            "unit": "iter/sec",
            "range": "stddev: 0.000015927191341929177",
            "extra": "mean: 59.635188000754624 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10250.259049612221,
            "unit": "iter/sec",
            "range": "stddev: 0.000024632471207764672",
            "extra": "mean: 97.55851000056737 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 282.58796467967363,
            "unit": "iter/sec",
            "range": "stddev: 0.0005389700199927683",
            "extra": "mean: 3.538721123999551 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "ce16cb8be7a39d5289a79fa5c8148192d049f169",
          "message": "Merge branch 'master' into dev",
          "timestamp": "2021-07-16T09:37:44+02:00",
          "tree_id": "45a6fd99afdb0d8abcfff697529960ca63d0b56d",
          "url": "https://github.com/simphony/osp-core/commit/ce16cb8be7a39d5289a79fa5c8148192d049f169"
        },
        "date": 1626421373614,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 153.4810940109784,
            "unit": "iter/sec",
            "range": "stddev: 0.005499067083623204",
            "extra": "mean: 6.51546046400002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 118.71690549155915,
            "unit": "iter/sec",
            "range": "stddev: 0.0038032919827539666",
            "extra": "mean: 8.423400153999976 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 123.10874358858862,
            "unit": "iter/sec",
            "range": "stddev: 0.0036321469130540366",
            "extra": "mean: 8.122899891999982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 219.55290425732719,
            "unit": "iter/sec",
            "range": "stddev: 0.0012968601180570187",
            "extra": "mean: 4.5547108719998946 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 265.81640066735133,
            "unit": "iter/sec",
            "range": "stddev: 0.0008783664351788409",
            "extra": "mean: 3.7619951119999655 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 377.6005219562938,
            "unit": "iter/sec",
            "range": "stddev: 0.0002681232361132372",
            "extra": "mean: 2.6483014240000102 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.48206325983641,
            "unit": "iter/sec",
            "range": "stddev: 0.010154817205381274",
            "extra": "mean: 95.40106515399971 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 416.29830303171286,
            "unit": "iter/sec",
            "range": "stddev: 0.05204530109428509",
            "extra": "mean: 2.4021236520001423 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 648.5359635267524,
            "unit": "iter/sec",
            "range": "stddev: 0.03283501469380578",
            "extra": "mean: 1.5419345360000989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 362.2708756532968,
            "unit": "iter/sec",
            "range": "stddev: 0.0004731433903029255",
            "extra": "mean: 2.7603654259997086 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.667842636157427,
            "unit": "iter/sec",
            "range": "stddev: 0.005516108621118718",
            "extra": "mean: 93.73966546999998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4481.535464399201,
            "unit": "iter/sec",
            "range": "stddev: 0.00012698044484805835",
            "extra": "mean: 223.1378079999331 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 6537.000383085306,
            "unit": "iter/sec",
            "range": "stddev: 0.00005041085213666513",
            "extra": "mean: 152.9753620005181 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15373.117711736999,
            "unit": "iter/sec",
            "range": "stddev: 0.000017072077495943997",
            "extra": "mean: 65.04861399952233 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9710.707912129763,
            "unit": "iter/sec",
            "range": "stddev: 0.00002810567284275061",
            "extra": "mean: 102.97910400032606 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 264.9987308760291,
            "unit": "iter/sec",
            "range": "stddev: 0.0005740070430639183",
            "extra": "mean: 3.7736029779999853 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "5e8239dfbf66477cdac06efec239bf68adcca115",
          "message": "Merge pull request #674 from simphony/dev\n\nMerge sprint 4.",
          "timestamp": "2021-07-16T12:01:38+02:00",
          "tree_id": "45a6fd99afdb0d8abcfff697529960ca63d0b56d",
          "url": "https://github.com/simphony/osp-core/commit/5e8239dfbf66477cdac06efec239bf68adcca115"
        },
        "date": 1626429891606,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 160.15366844423082,
            "unit": "iter/sec",
            "range": "stddev: 0.005602310860625093",
            "extra": "mean: 6.244003086000012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 131.0498503925347,
            "unit": "iter/sec",
            "range": "stddev: 0.0032424538010184406",
            "extra": "mean: 7.630684025999967 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 124.63163599475774,
            "unit": "iter/sec",
            "range": "stddev: 0.0038104358953398067",
            "extra": "mean: 8.02364497600001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 233.8979668143711,
            "unit": "iter/sec",
            "range": "stddev: 0.0011238342604571274",
            "extra": "mean: 4.275368501999985 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 287.7971012937707,
            "unit": "iter/sec",
            "range": "stddev: 0.0007020632271803908",
            "extra": "mean: 3.47467016000013 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 367.90937144232,
            "unit": "iter/sec",
            "range": "stddev: 0.0002526189866373446",
            "extra": "mean: 2.7180606900000583 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.69473338194705,
            "unit": "iter/sec",
            "range": "stddev: 0.009392184707566642",
            "extra": "mean: 93.50396725999944 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 469.86315706354884,
            "unit": "iter/sec",
            "range": "stddev: 0.046070933698467556",
            "extra": "mean: 2.1282792339999332 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 674.4851137459704,
            "unit": "iter/sec",
            "range": "stddev: 0.031555962577962324",
            "extra": "mean: 1.4826124099999447 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 389.3045340704626,
            "unit": "iter/sec",
            "range": "stddev: 0.0002645475192114304",
            "extra": "mean: 2.5686831580004252 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.080297429135687,
            "unit": "iter/sec",
            "range": "stddev: 0.00597619964717066",
            "extra": "mean: 90.25028492200002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4707.310362613071,
            "unit": "iter/sec",
            "range": "stddev: 0.00011768728232864519",
            "extra": "mean: 212.43553599998677 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7076.050532413564,
            "unit": "iter/sec",
            "range": "stddev: 0.000029348611088309462",
            "extra": "mean: 141.3217719996851 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15206.956489275886,
            "unit": "iter/sec",
            "range": "stddev: 0.000011884720274734438",
            "extra": "mean: 65.75937799948406 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9423.987240332774,
            "unit": "iter/sec",
            "range": "stddev: 0.000022755662670716672",
            "extra": "mean: 106.11219800046001 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 265.0140929167836,
            "unit": "iter/sec",
            "range": "stddev: 0.000860835119441595",
            "extra": "mean: 3.773384233999991 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "53036503+create-issue-branch[bot]@users.noreply.github.com",
            "name": "create-issue-branch[bot]",
            "username": "create-issue-branch[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3251c7101c0c9390227aaaea0457c453f394f30f",
          "message": "Regression: Ontology2dot broken (#676)\n\n* Fix ontology2dot not working.\r\n\r\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>",
          "timestamp": "2021-07-19T18:01:02+02:00",
          "tree_id": "2423445321b15bb2220d7cc9406ceea810400d30",
          "url": "https://github.com/simphony/osp-core/commit/3251c7101c0c9390227aaaea0457c453f394f30f"
        },
        "date": 1626710661850,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 156.2939188842576,
            "unit": "iter/sec",
            "range": "stddev: 0.005278377284528918",
            "extra": "mean: 6.398201587999998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.32342944312212,
            "unit": "iter/sec",
            "range": "stddev: 0.00380589241006783",
            "extra": "mean: 7.979353936000041 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 115.47061962528923,
            "unit": "iter/sec",
            "range": "stddev: 0.004509515490793039",
            "extra": "mean: 8.660211604 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 203.02685197249113,
            "unit": "iter/sec",
            "range": "stddev: 0.0017869831841988016",
            "extra": "mean: 4.9254568559999825 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 273.01130197118397,
            "unit": "iter/sec",
            "range": "stddev: 0.0008862334334838569",
            "extra": "mean: 3.6628520239999034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 357.54202472089526,
            "unit": "iter/sec",
            "range": "stddev: 0.0006116032109101097",
            "extra": "mean: 2.7968740199998052 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.55255955365623,
            "unit": "iter/sec",
            "range": "stddev: 0.011177333964260577",
            "extra": "mean: 94.76373906400006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 462.6078750099229,
            "unit": "iter/sec",
            "range": "stddev: 0.04680724488258578",
            "extra": "mean: 2.1616579700000784 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 666.8511532609849,
            "unit": "iter/sec",
            "range": "stddev: 0.031899644255102715",
            "extra": "mean: 1.4995850200001541 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 386.2302232803469,
            "unit": "iter/sec",
            "range": "stddev: 0.000292819322537033",
            "extra": "mean: 2.5891293319998567 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.933781326701048,
            "unit": "iter/sec",
            "range": "stddev: 0.0061196229701508415",
            "extra": "mean: 91.45966707400038 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4886.910775984781,
            "unit": "iter/sec",
            "range": "stddev: 0.0001090727556325959",
            "extra": "mean: 204.6282500008374 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 6935.221659191052,
            "unit": "iter/sec",
            "range": "stddev: 0.000046987321814664715",
            "extra": "mean: 144.19149799988418 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16247.989026825095,
            "unit": "iter/sec",
            "range": "stddev: 0.0000152410890749878",
            "extra": "mean: 61.546078000731086 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10490.203429781002,
            "unit": "iter/sec",
            "range": "stddev: 0.000016841462121873957",
            "extra": "mean: 95.32703600018522 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 273.2798954064695,
            "unit": "iter/sec",
            "range": "stddev: 0.00047639451760281135",
            "extra": "mean: 3.6592519860000152 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "53036503+create-issue-branch[bot]@users.noreply.github.com",
            "name": "create-issue-branch[bot]",
            "username": "create-issue-branch[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "fa6ebcd8b7f7b38b557d44cbeef40c98a11c722c",
          "message": "OSP-core incompatible with RDFLib 6.0.0 (#678)\n\n* Enforce `rdflib` < 6.0.0.\r\n\r\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>",
          "timestamp": "2021-07-21T15:21:48+02:00",
          "tree_id": "45c9a63b49c6592373287458baf78cbaeea58f9f",
          "url": "https://github.com/simphony/osp-core/commit/fa6ebcd8b7f7b38b557d44cbeef40c98a11c722c"
        },
        "date": 1626873902037,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 156.24354523736375,
            "unit": "iter/sec",
            "range": "stddev: 0.005269342076216083",
            "extra": "mean: 6.400264397999989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 124.26803227332425,
            "unit": "iter/sec",
            "range": "stddev: 0.0035345768519101273",
            "extra": "mean: 8.047121868000021 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 128.22427471958602,
            "unit": "iter/sec",
            "range": "stddev: 0.0035303184051666465",
            "extra": "mean: 7.798835299999961 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 223.42319727567445,
            "unit": "iter/sec",
            "range": "stddev: 0.0013519868665882384",
            "extra": "mean: 4.475810981999928 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 280.4841441973788,
            "unit": "iter/sec",
            "range": "stddev: 0.0007789872579310362",
            "extra": "mean: 3.565263922000142 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 345.695279212015,
            "unit": "iter/sec",
            "range": "stddev: 0.0007136685316580123",
            "extra": "mean: 2.892721018000074 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.10455353072455,
            "unit": "iter/sec",
            "range": "stddev: 0.006041814326220446",
            "extra": "mean: 90.05314776799963 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 416.88834774046336,
            "unit": "iter/sec",
            "range": "stddev: 0.05206233168991246",
            "extra": "mean: 2.3987237959995866 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 705.4166557866728,
            "unit": "iter/sec",
            "range": "stddev: 0.030150293742193662",
            "extra": "mean: 1.4176019120002366 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 381.62971335976243,
            "unit": "iter/sec",
            "range": "stddev: 0.00031740527735648493",
            "extra": "mean: 2.6203410399999427 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.737839159496556,
            "unit": "iter/sec",
            "range": "stddev: 0.010235971386528531",
            "extra": "mean: 93.12860671000078 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4647.938072879726,
            "unit": "iter/sec",
            "range": "stddev: 0.00011269351811479643",
            "extra": "mean: 215.14916600006018 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7568.67089161526,
            "unit": "iter/sec",
            "range": "stddev: 0.000021146083464503304",
            "extra": "mean: 132.12359399955176 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15743.51224046129,
            "unit": "iter/sec",
            "range": "stddev: 0.000019695394561980616",
            "extra": "mean: 63.51822799933871 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10117.004164909999,
            "unit": "iter/sec",
            "range": "stddev: 0.000019897327470944356",
            "extra": "mean: 98.84348999958092 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 282.26569188149045,
            "unit": "iter/sec",
            "range": "stddev: 0.00040665380381009545",
            "extra": "mean: 3.5427614079994214 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "1c15fdba15574256eea4a7eaa06faa0c8e447af2",
          "message": "Merge hotfix PRs #676, #678 (#681)\n\n* Regression: Ontology2dot broken (#676)\r\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\r\n(cherry picked from commit 3251c7101c0c9390227aaaea0457c453f394f30f)\r\n\r\n* OSP-core incompatible with RDFLib 6.0.0 (#678)\r\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\r\n(cherry picked from commit fa6ebcd8b7f7b38b557d44cbeef40c98a11c722c)\r\n\r\n* Bump OSP-core version to 3.5.5 in hotfix branch for bugfix release.\r\n\r\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>",
          "timestamp": "2021-07-27T09:52:29+02:00",
          "tree_id": "21e4adb4a817183500a60a1197e08afe63f1e44c",
          "url": "https://github.com/simphony/osp-core/commit/1c15fdba15574256eea4a7eaa06faa0c8e447af2"
        },
        "date": 1627372537783,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 157.98621773041413,
            "unit": "iter/sec",
            "range": "stddev: 0.0055213398480286535",
            "extra": "mean: 6.329666057999998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 129.00605318977657,
            "unit": "iter/sec",
            "range": "stddev: 0.0034422878001060604",
            "extra": "mean: 7.751574249999981 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 126.77488827485709,
            "unit": "iter/sec",
            "range": "stddev: 0.003715060375724768",
            "extra": "mean: 7.887997485999972 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 228.9071534822306,
            "unit": "iter/sec",
            "range": "stddev: 0.001220915527117433",
            "extra": "mean: 4.368583439999952 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 281.073843608885,
            "unit": "iter/sec",
            "range": "stddev: 0.0007278534428520906",
            "extra": "mean: 3.5577839160000337 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 397.0283864107852,
            "unit": "iter/sec",
            "range": "stddev: 0.00009330615358266413",
            "extra": "mean: 2.5187115940001092 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.10968225488144,
            "unit": "iter/sec",
            "range": "stddev: 0.007626917595635051",
            "extra": "mean: 90.01157522400013 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 461.76875712636934,
            "unit": "iter/sec",
            "range": "stddev: 0.047008171503374795",
            "extra": "mean: 2.1655860959998563 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 636.6035163235924,
            "unit": "iter/sec",
            "range": "stddev: 0.03366531247634316",
            "extra": "mean: 1.570836437999958 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 399.4790837489851,
            "unit": "iter/sec",
            "range": "stddev: 0.00026190649890868635",
            "extra": "mean: 2.5032599719998245 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.545245883733722,
            "unit": "iter/sec",
            "range": "stddev: 0.004110488813229428",
            "extra": "mean: 86.61573863999863 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5065.925831097823,
            "unit": "iter/sec",
            "range": "stddev: 0.00010507966705936245",
            "extra": "mean: 197.39728399918022 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8011.198886939597,
            "unit": "iter/sec",
            "range": "stddev: 0.00002066648645543596",
            "extra": "mean: 124.82526200045642 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15963.206978916169,
            "unit": "iter/sec",
            "range": "stddev: 0.00002546970670443302",
            "extra": "mean: 62.64405399997485 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10344.706731432208,
            "unit": "iter/sec",
            "range": "stddev: 0.000020166755921326365",
            "extra": "mean: 96.66779600058817 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 294.67709064864954,
            "unit": "iter/sec",
            "range": "stddev: 0.00035136927352268484",
            "extra": "mean: 3.3935451100008436 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "26eec531126eba9d881a5f1d8e30da7ec5632a92",
          "message": "* Regression: Ontology2dot broken (#676)\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\n(cherry picked from commit 3251c71)\n\n* OSP-core incompatible with RDFLib 6.0.0 (#678)\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\n(cherry picked from commit fa6ebcd)\n\n* Bump OSP-core version to 3.5.5 in hotfix branch for bugfix release.\n\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>",
          "timestamp": "2021-07-27T10:12:15+02:00",
          "tree_id": "21e4adb4a817183500a60a1197e08afe63f1e44c",
          "url": "https://github.com/simphony/osp-core/commit/26eec531126eba9d881a5f1d8e30da7ec5632a92"
        },
        "date": 1627373797223,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 161.88244784314256,
            "unit": "iter/sec",
            "range": "stddev: 0.0050717160420705246",
            "extra": "mean: 6.177321960000005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 129.07523005658496,
            "unit": "iter/sec",
            "range": "stddev: 0.003418446569156634",
            "extra": "mean: 7.74741985399997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 128.85726809874933,
            "unit": "iter/sec",
            "range": "stddev: 0.003710178190671015",
            "extra": "mean: 7.7605246080000185 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 222.5218249149982,
            "unit": "iter/sec",
            "range": "stddev: 0.00142819045615538",
            "extra": "mean: 4.493941213999989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 279.1756600942015,
            "unit": "iter/sec",
            "range": "stddev: 0.0008010725265271548",
            "extra": "mean: 3.581974157999923 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 384.90508787095854,
            "unit": "iter/sec",
            "range": "stddev: 0.0003028410808545624",
            "extra": "mean: 2.598043080000167 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 11.052066572756944,
            "unit": "iter/sec",
            "range": "stddev: 0.007975829490631513",
            "extra": "mean: 90.48081582000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 462.7308370377746,
            "unit": "iter/sec",
            "range": "stddev: 0.04682773856381262",
            "extra": "mean: 2.1610835499998586 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 646.7064639908809,
            "unit": "iter/sec",
            "range": "stddev: 0.03288793549274114",
            "extra": "mean: 1.546296589999912 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 382.7865851926917,
            "unit": "iter/sec",
            "range": "stddev: 0.0005048686223529013",
            "extra": "mean: 2.612421747999889 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.151375683635743,
            "unit": "iter/sec",
            "range": "stddev: 0.008703356931409832",
            "extra": "mean: 89.67503457599992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4993.187694163713,
            "unit": "iter/sec",
            "range": "stddev: 0.00010848208197533271",
            "extra": "mean: 200.2728640000555 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7695.913997609079,
            "unit": "iter/sec",
            "range": "stddev: 0.00002243748532642724",
            "extra": "mean: 129.9390819999644 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15605.056250508464,
            "unit": "iter/sec",
            "range": "stddev: 0.00001780974643665101",
            "extra": "mean: 64.08179399977598 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 8445.49071683324,
            "unit": "iter/sec",
            "range": "stddev: 0.00005418454614469012",
            "extra": "mean: 118.40638200061449 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 293.9532372841078,
            "unit": "iter/sec",
            "range": "stddev: 0.00026835642555208205",
            "extra": "mean: 3.4019016399996076 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "53036503+create-issue-branch[bot]@users.noreply.github.com",
            "name": "create-issue-branch[bot]",
            "username": "create-issue-branch[bot]"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "46c988520960b3db9da40304cfc7634952a7d084",
          "message": "Support RDFLib 6.0.0 (#680)\n\n* Support both `rdflib >= 5.0.0, < 6.0.0` and `rdflib >= 6.0.0, < 7.0.0`, for `python_version < '3.7'` and `python_version >= '3.7'` respectively.\r\n* Require rdflib >= 6.0.0, < 7.0.0 for people having python >= 3.7.\r\n* The update brings [significant performance improvements](https://github.com/simphony/osp-core/pull/680#issuecomment-885556834).\r\n\r\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\r\nAuthored-by: José Manuel Domínguez <43052541+kysrpex@users.noreply.github.com>",
          "timestamp": "2021-07-27T12:25:46+02:00",
          "tree_id": "0df604bb78c7ad7da9952ca316e4efdc450f7a94",
          "url": "https://github.com/simphony/osp-core/commit/46c988520960b3db9da40304cfc7634952a7d084"
        },
        "date": 1627381664314,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 291.3115968415943,
            "unit": "iter/sec",
            "range": "stddev: 0.00505148078065747",
            "extra": "mean: 3.432750398000006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 155.42471975178407,
            "unit": "iter/sec",
            "range": "stddev: 0.0033522696326397624",
            "extra": "mean: 6.433982969999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 150.96081840369285,
            "unit": "iter/sec",
            "range": "stddev: 0.0037808953589165413",
            "extra": "mean: 6.6242354179999445 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 285.0058780353448,
            "unit": "iter/sec",
            "range": "stddev: 0.0014029944109649822",
            "extra": "mean: 3.5086995639998193 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 355.3764407751552,
            "unit": "iter/sec",
            "range": "stddev: 0.0009406422691503151",
            "extra": "mean: 2.8139175400000553 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 555.8689890790113,
            "unit": "iter/sec",
            "range": "stddev: 0.00017669283179405743",
            "extra": "mean: 1.7989850479999703 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 23.703891785200398,
            "unit": "iter/sec",
            "range": "stddev: 0.004139756043702439",
            "extra": "mean: 42.18716525800009 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 534.3265063863806,
            "unit": "iter/sec",
            "range": "stddev: 0.040337307097060966",
            "extra": "mean: 1.8715148660000835 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 748.4435274849022,
            "unit": "iter/sec",
            "range": "stddev: 0.02822770191844189",
            "extra": "mean: 1.3361061499996367 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 596.1996879707716,
            "unit": "iter/sec",
            "range": "stddev: 0.00010755215420056078",
            "extra": "mean: 1.6772903780000377 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 23.230426248292847,
            "unit": "iter/sec",
            "range": "stddev: 0.003761503891550911",
            "extra": "mean: 43.04699316800043 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6882.300425997338,
            "unit": "iter/sec",
            "range": "stddev: 0.00007834740616779467",
            "extra": "mean: 145.30025399974988 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9715.761133135786,
            "unit": "iter/sec",
            "range": "stddev: 0.00002211863668065632",
            "extra": "mean: 102.92554399978826 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16560.255433327107,
            "unit": "iter/sec",
            "range": "stddev: 0.00001894856294869124",
            "extra": "mean: 60.3855420000059 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14686.93922514689,
            "unit": "iter/sec",
            "range": "stddev: 0.00001905828107621973",
            "extra": "mean: 68.08770599988634 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 540.6263277105646,
            "unit": "iter/sec",
            "range": "stddev: 0.0003976561758551208",
            "extra": "mean: 1.8497064400004035 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "3fe52c34d2621ce20c24c7f18e4a3a642df63ec2",
          "message": "Infer ontology format from file extension (#699)",
          "timestamp": "2021-08-27T14:02:34+02:00",
          "tree_id": "0b7f8c04f4d7a350cc993e46c6afb53ebb746a0b",
          "url": "https://github.com/simphony/osp-core/commit/3fe52c34d2621ce20c24c7f18e4a3a642df63ec2"
        },
        "date": 1630065878841,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 287.4609791124471,
            "unit": "iter/sec",
            "range": "stddev: 0.005569435857023758",
            "extra": "mean: 3.47873302 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 165.22841418035875,
            "unit": "iter/sec",
            "range": "stddev: 0.0027972483864435976",
            "extra": "mean: 6.052227790000016 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 155.25828744634427,
            "unit": "iter/sec",
            "range": "stddev: 0.0033941906301663714",
            "extra": "mean: 6.440880010000047 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 277.0942840855889,
            "unit": "iter/sec",
            "range": "stddev: 0.0010197953431544515",
            "extra": "mean: 3.6088799279999577 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 402.4323001783945,
            "unit": "iter/sec",
            "range": "stddev: 0.000587447116905601",
            "extra": "mean: 2.4848900039999506 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 577.787539973339,
            "unit": "iter/sec",
            "range": "stddev: 0.00022141764611459234",
            "extra": "mean: 1.7307399879999892 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 24.069474711786057,
            "unit": "iter/sec",
            "range": "stddev: 0.0036280097481363564",
            "extra": "mean: 41.54639899600018 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 489.17156087131195,
            "unit": "iter/sec",
            "range": "stddev: 0.04412848547399861",
            "extra": "mean: 2.044272562000131 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 872.9915802932654,
            "unit": "iter/sec",
            "range": "stddev: 0.024047802030469752",
            "extra": "mean: 1.1454864199996848 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 613.1694030002608,
            "unit": "iter/sec",
            "range": "stddev: 0.00008818101190929666",
            "extra": "mean: 1.6308706780001785 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 24.526870337132355,
            "unit": "iter/sec",
            "range": "stddev: 0.0033582347184151345",
            "extra": "mean: 40.77161033000016 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7165.053865556911,
            "unit": "iter/sec",
            "range": "stddev: 0.00007299664480780023",
            "extra": "mean: 139.56629200055204 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9629.887411022975,
            "unit": "iter/sec",
            "range": "stddev: 0.000022890602028956004",
            "extra": "mean: 103.84337399992205 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15490.504181630122,
            "unit": "iter/sec",
            "range": "stddev: 0.000022662216365358197",
            "extra": "mean: 64.5556779995502 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14704.553753289703,
            "unit": "iter/sec",
            "range": "stddev: 0.000019129742593493905",
            "extra": "mean: 68.00614399986671 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 597.1914323424747,
            "unit": "iter/sec",
            "range": "stddev: 0.00013294263673717234",
            "extra": "mean: 1.674504933999998 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "398428e88322f60100cad3bd51d2ceef7e21608a",
          "message": "Change of attributes for added individuals (#698)\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\n(merged from 2d71d21)",
          "timestamp": "2021-09-01T17:40:42+02:00",
          "tree_id": "cc1c8610c1bd23df4dd039903593e83896ecea3e",
          "url": "https://github.com/simphony/osp-core/commit/398428e88322f60100cad3bd51d2ceef7e21608a"
        },
        "date": 1630511579236,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 136.64682699948648,
            "unit": "iter/sec",
            "range": "stddev: 0.007783676826874716",
            "extra": "mean: 7.318135532000007 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 96.90321145314729,
            "unit": "iter/sec",
            "range": "stddev: 0.006182959898938153",
            "extra": "mean: 10.319575430000068 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 101.47061051406197,
            "unit": "iter/sec",
            "range": "stddev: 0.005467040351700866",
            "extra": "mean: 9.855070300000001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 221.39615293073842,
            "unit": "iter/sec",
            "range": "stddev: 0.0015187802740972958",
            "extra": "mean: 4.51679031799997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 268.6629303909847,
            "unit": "iter/sec",
            "range": "stddev: 0.0013127153638848531",
            "extra": "mean: 3.722136130000152 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 346.12300741928277,
            "unit": "iter/sec",
            "range": "stddev: 0.000771145247620635",
            "extra": "mean: 2.8891462819997713 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.461025333696977,
            "unit": "iter/sec",
            "range": "stddev: 0.01674042734820773",
            "extra": "mean: 95.59292402999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 433.98767611097924,
            "unit": "iter/sec",
            "range": "stddev: 0.049955889252221976",
            "extra": "mean: 2.304212896000024 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 704.6578294045291,
            "unit": "iter/sec",
            "range": "stddev: 0.030122948691056667",
            "extra": "mean: 1.4191284879997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 390.93045320409135,
            "unit": "iter/sec",
            "range": "stddev: 0.00036936553636259266",
            "extra": "mean: 2.5579997460006894 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.516310268350493,
            "unit": "iter/sec",
            "range": "stddev: 0.012071637063644301",
            "extra": "mean: 95.09038574199963 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4411.646616482133,
            "unit": "iter/sec",
            "range": "stddev: 0.00013633353149428195",
            "extra": "mean: 226.67273400003296 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7672.594200955981,
            "unit": "iter/sec",
            "range": "stddev: 0.00002702779700560227",
            "extra": "mean: 130.33401399951572 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16487.64219881852,
            "unit": "iter/sec",
            "range": "stddev: 0.000017965762701673118",
            "extra": "mean: 60.65148600032444 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 10447.895207809128,
            "unit": "iter/sec",
            "range": "stddev: 0.00002228005391578563",
            "extra": "mean: 95.71305799971697 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 264.74736223770515,
            "unit": "iter/sec",
            "range": "stddev: 0.0007789531613296508",
            "extra": "mean: 3.7771858860000407 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "6f92f04b0beac92fd2cc3b307c9ec9286ef290bb",
          "message": "Get FOAF ontology from web archive (#702)\n\n* Change URL on `foaf.yml` to the web archive (29 Aug 2021).\r\n\r\n* Change URL on `test_installation.py` to the web archive (29 Aug 2021).",
          "timestamp": "2021-09-02T09:41:27+02:00",
          "tree_id": "c53a49ac895601ea51e3d7494b76ad4e3b896f5d",
          "url": "https://github.com/simphony/osp-core/commit/6f92f04b0beac92fd2cc3b307c9ec9286ef290bb"
        },
        "date": 1630568647775,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 320.58737084535863,
            "unit": "iter/sec",
            "range": "stddev: 0.005377718695757716",
            "extra": "mean: 3.119274466 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 159.22451602521355,
            "unit": "iter/sec",
            "range": "stddev: 0.00287963408252707",
            "extra": "mean: 6.280439877999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 144.40236971739765,
            "unit": "iter/sec",
            "range": "stddev: 0.0034459425814955627",
            "extra": "mean: 6.92509411000005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 234.00375640427225,
            "unit": "iter/sec",
            "range": "stddev: 0.0015102728943169207",
            "extra": "mean: 4.273435671999934 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 373.4768297443434,
            "unit": "iter/sec",
            "range": "stddev: 0.0006430844856254366",
            "extra": "mean: 2.6775422740000536 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 547.5930086588291,
            "unit": "iter/sec",
            "range": "stddev: 0.000317046158532304",
            "extra": "mean: 1.8261737900000057 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 21.38943451960297,
            "unit": "iter/sec",
            "range": "stddev: 0.006374768538127084",
            "extra": "mean: 46.75205410799995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 413.78610538354826,
            "unit": "iter/sec",
            "range": "stddev: 0.05253320569431479",
            "extra": "mean: 2.416707537999798 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 710.3675097677469,
            "unit": "iter/sec",
            "range": "stddev: 0.029970609625824363",
            "extra": "mean: 1.4077220400000385 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 570.448467943245,
            "unit": "iter/sec",
            "range": "stddev: 0.0002353054569703894",
            "extra": "mean: 1.753006723999988 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 23.02600284958299,
            "unit": "iter/sec",
            "range": "stddev: 0.004057765526718895",
            "extra": "mean: 43.42916165399981 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7642.18320052134,
            "unit": "iter/sec",
            "range": "stddev: 0.00006335972698148165",
            "extra": "mean: 130.85266000058482 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9852.752389039173,
            "unit": "iter/sec",
            "range": "stddev: 0.000021753224686346",
            "extra": "mean: 101.49448200002098 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16996.32223380495,
            "unit": "iter/sec",
            "range": "stddev: 0.00001646523709489359",
            "extra": "mean: 58.83625800004211 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 15086.461415527303,
            "unit": "iter/sec",
            "range": "stddev: 0.00001793727577170194",
            "extra": "mean: 66.2845960001448 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 585.0005418802035,
            "unit": "iter/sec",
            "range": "stddev: 0.0002372756790751626",
            "extra": "mean: 1.7094001259998493 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "9ef9cf2adca43cce434f42cf56e7f57232c34a25",
          "message": "684 Error when installing ontologies (wrong encoding) (#697)\n\n* Make OWL parser read files in bytes mode from local disk. In such a way bytes are sent to rdflib which will handle the encoding. Previously, they were read in text mode, using the default encoding of the OS, leading to errors on Windows.\r\n\r\n* Bump package version to 3.5.6.",
          "timestamp": "2021-09-02T09:57:58+02:00",
          "tree_id": "e430e6b084626e97cc78e1f5271ba3fcefb8564f",
          "url": "https://github.com/simphony/osp-core/commit/9ef9cf2adca43cce434f42cf56e7f57232c34a25"
        },
        "date": 1630569609046,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 280.0907132033582,
            "unit": "iter/sec",
            "range": "stddev: 0.005826507104895408",
            "extra": "mean: 3.5702718899999946 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 153.74288545957313,
            "unit": "iter/sec",
            "range": "stddev: 0.0033914636723574006",
            "extra": "mean: 6.504366020000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 151.28430015420528,
            "unit": "iter/sec",
            "range": "stddev: 0.0028014449328266993",
            "extra": "mean: 6.61007123000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 275.2480131994187,
            "unit": "iter/sec",
            "range": "stddev: 0.0015548483623301405",
            "extra": "mean: 3.6330870780000666 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 389.4433188312303,
            "unit": "iter/sec",
            "range": "stddev: 0.0006538066212404773",
            "extra": "mean: 2.5677677639999814 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 548.9185327829107,
            "unit": "iter/sec",
            "range": "stddev: 0.00029547835197549986",
            "extra": "mean: 1.8217639600000268 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 23.176188967677486,
            "unit": "iter/sec",
            "range": "stddev: 0.006304180921543873",
            "extra": "mean: 43.147732416000025 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 459.820012707631,
            "unit": "iter/sec",
            "range": "stddev: 0.047198065534472686",
            "extra": "mean: 2.1747639779998735 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 902.4254975603546,
            "unit": "iter/sec",
            "range": "stddev: 0.023330891909658015",
            "extra": "mean: 1.1081247179999139 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 590.6787039836076,
            "unit": "iter/sec",
            "range": "stddev: 0.00017057798098012075",
            "extra": "mean: 1.6929677559998026 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.28441069426951,
            "unit": "iter/sec",
            "range": "stddev: 0.009978926394715208",
            "extra": "mean: 44.87441977799989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6520.748997239624,
            "unit": "iter/sec",
            "range": "stddev: 0.00007786717701194264",
            "extra": "mean: 153.35661599968375 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7952.295768109758,
            "unit": "iter/sec",
            "range": "stddev: 0.00004798015443100152",
            "extra": "mean: 125.74985000057382 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14746.064076412218,
            "unit": "iter/sec",
            "range": "stddev: 0.000027617165374175637",
            "extra": "mean: 67.814706000064 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14017.412598168989,
            "unit": "iter/sec",
            "range": "stddev: 0.000021059110199333104",
            "extra": "mean: 71.33984199984411 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 535.474038593375,
            "unit": "iter/sec",
            "range": "stddev: 0.0003410400583564741",
            "extra": "mean: 1.8675041700002453 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "398428e88322f60100cad3bd51d2ceef7e21608a",
          "message": "Change of attributes for added individuals (#698)\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\n(merged from 2d71d21)",
          "timestamp": "2021-09-01T17:40:42+02:00",
          "tree_id": "cc1c8610c1bd23df4dd039903593e83896ecea3e",
          "url": "https://github.com/simphony/osp-core/commit/398428e88322f60100cad3bd51d2ceef7e21608a"
        },
        "date": 1630911508508,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 141.45969030274154,
            "unit": "iter/sec",
            "range": "stddev: 0.0054382482461264895",
            "extra": "mean: 7.069151627999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 107.92366101773571,
            "unit": "iter/sec",
            "range": "stddev: 0.004697535266923111",
            "extra": "mean: 9.265808725999985 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 126.85270391018814,
            "unit": "iter/sec",
            "range": "stddev: 0.003322712255445326",
            "extra": "mean: 7.883158728000005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 233.82125511424653,
            "unit": "iter/sec",
            "range": "stddev: 0.0012407930427409742",
            "extra": "mean: 4.27677115800013 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 256.96169621031726,
            "unit": "iter/sec",
            "range": "stddev: 0.0013355205493754269",
            "extra": "mean: 3.8916306000000986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 344.7819962779913,
            "unit": "iter/sec",
            "range": "stddev: 0.0007825979345396903",
            "extra": "mean: 2.9003834619999083 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.452764519786463,
            "unit": "iter/sec",
            "range": "stddev: 0.01463386318027106",
            "extra": "mean: 95.66847106400029 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 399.0201367841573,
            "unit": "iter/sec",
            "range": "stddev: 0.05450564648006013",
            "extra": "mean: 2.5061391840004603 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 618.0279784774293,
            "unit": "iter/sec",
            "range": "stddev: 0.03472001240019072",
            "extra": "mean: 1.6180497240005138 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 355.0939415119642,
            "unit": "iter/sec",
            "range": "stddev: 0.0007938264423998444",
            "extra": "mean: 2.816156185999887 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 9.68762193250267,
            "unit": "iter/sec",
            "range": "stddev: 0.020749984112774966",
            "extra": "mean: 103.22450720799992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 2890.8770298215427,
            "unit": "iter/sec",
            "range": "stddev: 0.00011866707475782272",
            "extra": "mean: 345.91578599997774 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 6034.554340934531,
            "unit": "iter/sec",
            "range": "stddev: 0.00005058202444327966",
            "extra": "mean: 165.71231999961356 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 12000.608766741227,
            "unit": "iter/sec",
            "range": "stddev: 0.000047278618589324766",
            "extra": "mean: 83.3291060009742 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 4879.875234464278,
            "unit": "iter/sec",
            "range": "stddev: 0.00003700524745998585",
            "extra": "mean: 204.92327200037153 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 240.49830517722722,
            "unit": "iter/sec",
            "range": "stddev: 0.0010180440367446655",
            "extra": "mean: 4.15803345999916 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "7582e78bad4063e3e568af6cfa578ef62af28279",
          "message": "FOAF back online, get from official website again (#703)\n\nRevert: Get FOAF ontology from web archive (#702).\r\n\r\nThis reverts commit 6f92f04b0beac92fd2cc3b307c9ec9286ef290bb.",
          "timestamp": "2021-09-06T13:02:00+02:00",
          "tree_id": "e430e6b084626e97cc78e1f5271ba3fcefb8564f",
          "url": "https://github.com/simphony/osp-core/commit/7582e78bad4063e3e568af6cfa578ef62af28279"
        },
        "date": 1630926263170,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 272.35205340233745,
            "unit": "iter/sec",
            "range": "stddev: 0.005693160555345142",
            "extra": "mean: 3.671718232 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 149.94200511638329,
            "unit": "iter/sec",
            "range": "stddev: 0.0033142564887922743",
            "extra": "mean: 6.669245213999982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 146.9772531856391,
            "unit": "iter/sec",
            "range": "stddev: 0.003114418411626245",
            "extra": "mean: 6.803773905999954 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 282.208197349036,
            "unit": "iter/sec",
            "range": "stddev: 0.0011715928240390693",
            "extra": "mean: 3.5434831779999527 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 304.8143113645249,
            "unit": "iter/sec",
            "range": "stddev: 0.0013332534224703078",
            "extra": "mean: 3.2806858560000762 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 452.197523322072,
            "unit": "iter/sec",
            "range": "stddev: 0.000801936672222982",
            "extra": "mean: 2.2114229920002515 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 19.265697878780355,
            "unit": "iter/sec",
            "range": "stddev: 0.013788411900521567",
            "extra": "mean: 51.90572416800022 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 390.8051813395263,
            "unit": "iter/sec",
            "range": "stddev: 0.05565250414114476",
            "extra": "mean: 2.55881970799976 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 772.5984199568428,
            "unit": "iter/sec",
            "range": "stddev: 0.0273491704681497",
            "extra": "mean: 1.2943334779999418 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 485.7246822486138,
            "unit": "iter/sec",
            "range": "stddev: 0.0005970277336334255",
            "extra": "mean: 2.0587794620001603 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 17.07257104215925,
            "unit": "iter/sec",
            "range": "stddev: 0.016474320289935278",
            "extra": "mean: 58.57348594599992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5763.637668721834,
            "unit": "iter/sec",
            "range": "stddev: 0.00008626834650465737",
            "extra": "mean: 173.50153800035173 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7635.189310903476,
            "unit": "iter/sec",
            "range": "stddev: 0.00003563827161095687",
            "extra": "mean: 130.97252200046228 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 13661.828166266467,
            "unit": "iter/sec",
            "range": "stddev: 0.000031520990934964994",
            "extra": "mean: 73.19664600007059 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12044.843433889342,
            "unit": "iter/sec",
            "range": "stddev: 0.00003087630258373136",
            "extra": "mean: 83.02308000006065 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 470.8645137734923,
            "unit": "iter/sec",
            "range": "stddev: 0.0007225599384185021",
            "extra": "mean: 2.1237531619999004 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "80e8f5b63ca7920cbb13602e793d53b58b6ceb78",
          "message": "Change of attributes for added individuals (#698)\n\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\r\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>",
          "timestamp": "2021-09-08T12:04:34+02:00",
          "tree_id": "9b5bac86c779e0a2de41887d46923963f7b0869c",
          "url": "https://github.com/simphony/osp-core/commit/80e8f5b63ca7920cbb13602e793d53b58b6ceb78"
        },
        "date": 1631095591959,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 303.2419874401515,
            "unit": "iter/sec",
            "range": "stddev: 0.005674525218394307",
            "extra": "mean: 3.297696365999983 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 164.67457760724662,
            "unit": "iter/sec",
            "range": "stddev: 0.0026748158585702167",
            "extra": "mean: 6.072582753999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 152.48406730043385,
            "unit": "iter/sec",
            "range": "stddev: 0.003983214213602068",
            "extra": "mean: 6.558062213999946 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 295.3040869886636,
            "unit": "iter/sec",
            "range": "stddev: 0.001156502932723015",
            "extra": "mean: 3.386339857999964 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 360.07317430094145,
            "unit": "iter/sec",
            "range": "stddev: 0.0008482054155335479",
            "extra": "mean: 2.777213275999898 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 574.5327370063342,
            "unit": "iter/sec",
            "range": "stddev: 0.00030290512424363417",
            "extra": "mean: 1.7405448560000423 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 23.305409640750977,
            "unit": "iter/sec",
            "range": "stddev: 0.00559453854245272",
            "extra": "mean: 42.908492723999885 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 525.2839244970862,
            "unit": "iter/sec",
            "range": "stddev: 0.04104850831444003",
            "extra": "mean: 1.9037323499998848 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 828.5110716345504,
            "unit": "iter/sec",
            "range": "stddev: 0.025406469366733353",
            "extra": "mean: 1.206984473999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 504.83083173854567,
            "unit": "iter/sec",
            "range": "stddev: 0.0005606590566175923",
            "extra": "mean: 1.9808615820000173 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 23.75025596185227,
            "unit": "iter/sec",
            "range": "stddev: 0.005649291781692368",
            "extra": "mean: 42.10480938000006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7433.820266401484,
            "unit": "iter/sec",
            "range": "stddev: 0.00006384592048548114",
            "extra": "mean: 134.52033600000846 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9607.061020784258,
            "unit": "iter/sec",
            "range": "stddev: 0.000020427819117426234",
            "extra": "mean: 104.09010599980206 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16540.804378062225,
            "unit": "iter/sec",
            "range": "stddev: 0.000014940216330101172",
            "extra": "mean: 60.45655199974931 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 13909.4528557631,
            "unit": "iter/sec",
            "range": "stddev: 0.0000177433140901294",
            "extra": "mean: 71.89355400026898 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 535.4274985076204,
            "unit": "iter/sec",
            "range": "stddev: 0.0003136449270861497",
            "extra": "mean: 1.8676664960004246 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "19f233ebe6c40e92884aa07bf498304d772f7f27",
          "message": "Force `rdflib-jsonld==0.6.1` for `python_version < '3.7'`. Force `websockets < 10` (#704)\n\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\n(merged from 0701e09)",
          "timestamp": "2021-09-22T11:20:24+02:00",
          "tree_id": "ac12e73e98a716a039af52e7e65db2b972e4db68",
          "url": "https://github.com/simphony/osp-core/commit/19f233ebe6c40e92884aa07bf498304d772f7f27"
        },
        "date": 1632302694208,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 151.86664290241262,
            "unit": "iter/sec",
            "range": "stddev: 0.006057502849003891",
            "extra": "mean: 6.58472447199999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 117.12361717398156,
            "unit": "iter/sec",
            "range": "stddev: 0.004338222915905363",
            "extra": "mean: 8.53798767600003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 110.84013717350075,
            "unit": "iter/sec",
            "range": "stddev: 0.005032691726240932",
            "extra": "mean: 9.02200254800006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 188.69548982851333,
            "unit": "iter/sec",
            "range": "stddev: 0.002078271331922991",
            "extra": "mean: 5.299543730000124 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 217.93996489296103,
            "unit": "iter/sec",
            "range": "stddev: 0.0016210421317463634",
            "extra": "mean: 4.588419570000113 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 369.5960983022909,
            "unit": "iter/sec",
            "range": "stddev: 0.000620535887573144",
            "extra": "mean: 2.705656268000169 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 9.674608873158917,
            "unit": "iter/sec",
            "range": "stddev: 0.021010795134461625",
            "extra": "mean: 103.36335175000039 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 392.3414493961912,
            "unit": "iter/sec",
            "range": "stddev: 0.055379196181839625",
            "extra": "mean: 2.5488002899999174 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 724.3166251910162,
            "unit": "iter/sec",
            "range": "stddev: 0.028982237305894824",
            "extra": "mean: 1.3806116899999097 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 350.4615193051561,
            "unit": "iter/sec",
            "range": "stddev: 0.0007935347106800482",
            "extra": "mean: 2.8533803140003897 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 10.14655531260239,
            "unit": "iter/sec",
            "range": "stddev: 0.01721372643956397",
            "extra": "mean: 98.55561510200056 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 3305.8580167663804,
            "unit": "iter/sec",
            "range": "stddev: 0.00021765532608021099",
            "extra": "mean: 302.4933300003454 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 4941.3467575452805,
            "unit": "iter/sec",
            "range": "stddev: 0.00008224028165060576",
            "extra": "mean: 202.37397799962764 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 9818.912545180692,
            "unit": "iter/sec",
            "range": "stddev: 0.00004323836966451835",
            "extra": "mean: 101.84427200044865 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 8947.44094242471,
            "unit": "iter/sec",
            "range": "stddev: 0.00004332161502584957",
            "extra": "mean: 111.76379999989194 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 215.91669489639767,
            "unit": "iter/sec",
            "range": "stddev: 0.0014073291692187873",
            "extra": "mean: 4.631415836000201 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f79273400f5cd29f97e02c2ebfd1f7b8442dd610",
          "message": "Force `rdflib-jsonld==0.6.1` for `python_version < '3.7'`. Force `websockets < 10` (#704)",
          "timestamp": "2021-09-22T11:37:37+02:00",
          "tree_id": "9383ed3c2fbc9d4d41693743878bb146ad7cd2d8",
          "url": "https://github.com/simphony/osp-core/commit/f79273400f5cd29f97e02c2ebfd1f7b8442dd610"
        },
        "date": 1632303579180,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 294.9088211582446,
            "unit": "iter/sec",
            "range": "stddev: 0.0058908308917951235",
            "extra": "mean: 3.3908785639999954 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 150.94951905789569,
            "unit": "iter/sec",
            "range": "stddev: 0.003278550991472061",
            "extra": "mean: 6.624731276000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 140.50958174995677,
            "unit": "iter/sec",
            "range": "stddev: 0.004205448033526324",
            "extra": "mean: 7.116952363999957 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 265.542293184999,
            "unit": "iter/sec",
            "range": "stddev: 0.0013483512693486619",
            "extra": "mean: 3.7658784519997965 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 310.602513134756,
            "unit": "iter/sec",
            "range": "stddev: 0.0012205184475245923",
            "extra": "mean: 3.2195489659999836 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 546.0852576438581,
            "unit": "iter/sec",
            "range": "stddev: 0.00042251646031084495",
            "extra": "mean: 1.8312158879999885 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 22.113955894315602,
            "unit": "iter/sec",
            "range": "stddev: 0.00914375784364871",
            "extra": "mean: 45.22031267400014 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 521.3644097844656,
            "unit": "iter/sec",
            "range": "stddev: 0.04130732645956753",
            "extra": "mean: 1.9180442340001775 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 795.6389324264977,
            "unit": "iter/sec",
            "range": "stddev: 0.026470313686130193",
            "extra": "mean: 1.25685151799982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 535.0106072808753,
            "unit": "iter/sec",
            "range": "stddev: 0.0005326036709068893",
            "extra": "mean: 1.869121819999748 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.34897018115932,
            "unit": "iter/sec",
            "range": "stddev: 0.00857044476626603",
            "extra": "mean: 44.74479100800011 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 8081.191276210043,
            "unit": "iter/sec",
            "range": "stddev: 0.0000619073006259269",
            "extra": "mean: 123.74413199992775 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 10262.443520651028,
            "unit": "iter/sec",
            "range": "stddev: 0.00001764678565324158",
            "extra": "mean: 97.44267999991507 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16118.733427274825,
            "unit": "iter/sec",
            "range": "stddev: 0.000019128009038316682",
            "extra": "mean: 62.03961400018443 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14486.54960097048,
            "unit": "iter/sec",
            "range": "stddev: 0.0000165627577995061",
            "extra": "mean: 69.02954999947042 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 563.047935588174,
            "unit": "iter/sec",
            "range": "stddev: 0.0003676979837356272",
            "extra": "mean: 1.7760477160001926 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f79273400f5cd29f97e02c2ebfd1f7b8442dd610",
          "message": "Force `rdflib-jsonld==0.6.1` for `python_version < '3.7'`. Force `websockets < 10` (#704)",
          "timestamp": "2021-09-22T11:37:37+02:00",
          "tree_id": "9383ed3c2fbc9d4d41693743878bb146ad7cd2d8",
          "url": "https://github.com/simphony/osp-core/commit/f79273400f5cd29f97e02c2ebfd1f7b8442dd610"
        },
        "date": 1632406261154,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 253.62427774044804,
            "unit": "iter/sec",
            "range": "stddev: 0.005449727858991207",
            "extra": "mean: 3.9428402080000082 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 157.69720638376998,
            "unit": "iter/sec",
            "range": "stddev: 0.003256137110911644",
            "extra": "mean: 6.341266424000006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 133.52300161773545,
            "unit": "iter/sec",
            "range": "stddev: 0.004567014630036282",
            "extra": "mean: 7.489346313999977 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 298.2092283552216,
            "unit": "iter/sec",
            "range": "stddev: 0.001042963203456704",
            "extra": "mean: 3.3533502820000507 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 410.8489486617407,
            "unit": "iter/sec",
            "range": "stddev: 0.0005865717994841076",
            "extra": "mean: 2.4339845659999924 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 566.4673635085077,
            "unit": "iter/sec",
            "range": "stddev: 0.0004067694740526043",
            "extra": "mean: 1.7653267680000795 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 23.203672617046557,
            "unit": "iter/sec",
            "range": "stddev: 0.008150863110423486",
            "extra": "mean: 43.09662597399995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 445.4970418871866,
            "unit": "iter/sec",
            "range": "stddev: 0.048606628764425744",
            "extra": "mean: 2.244683815999906 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 920.6673892126921,
            "unit": "iter/sec",
            "range": "stddev: 0.02264375856205543",
            "extra": "mean: 1.0861685899998577 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 551.8453490493619,
            "unit": "iter/sec",
            "range": "stddev: 0.0004721143250526134",
            "extra": "mean: 1.8121018899998944 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.20008756275759,
            "unit": "iter/sec",
            "range": "stddev: 0.009239089090631654",
            "extra": "mean: 45.04486737599987 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 8224.960567485981,
            "unit": "iter/sec",
            "range": "stddev: 0.00006090348662167895",
            "extra": "mean: 121.58112999995296 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 10247.692255604994,
            "unit": "iter/sec",
            "range": "stddev: 0.0000210083604575347",
            "extra": "mean: 97.58294599967599 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16771.16612571931,
            "unit": "iter/sec",
            "range": "stddev: 0.000020128176146794756",
            "extra": "mean: 59.62614599985727 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14048.549482979999,
            "unit": "iter/sec",
            "range": "stddev: 0.000023926840936826465",
            "extra": "mean: 71.18172600036132 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 501.65971306780415,
            "unit": "iter/sec",
            "range": "stddev: 0.0006671889798302535",
            "extra": "mean: 1.9933831119997476 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "jose.manuel.dominguez@iwm.fraunhofer.de",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "distinct": true,
          "id": "19f233ebe6c40e92884aa07bf498304d772f7f27",
          "message": "Force `rdflib-jsonld==0.6.1` for `python_version < '3.7'`. Force `websockets < 10` (#704)\n\nAuthored-by: kysrpex <kysrpex@users.noreply.github.com>\nAuthored-by: José Manuel Domínguez <jose.manuel.dominguez@iwm.fraunhofer.de>\n(merged from 0701e09)",
          "timestamp": "2021-09-22T11:20:24+02:00",
          "tree_id": "ac12e73e98a716a039af52e7e65db2b972e4db68",
          "url": "https://github.com/simphony/osp-core/commit/19f233ebe6c40e92884aa07bf498304d772f7f27"
        },
        "date": 1632406327491,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 165.2248883506114,
            "unit": "iter/sec",
            "range": "stddev: 0.005264499850753359",
            "extra": "mean: 6.052356942000013 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 123.56098751776862,
            "unit": "iter/sec",
            "range": "stddev: 0.0035838565088686398",
            "extra": "mean: 8.09316937399999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 131.32784841856392,
            "unit": "iter/sec",
            "range": "stddev: 0.0034793420489072466",
            "extra": "mean: 7.614531206000056 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 218.84716925106002,
            "unit": "iter/sec",
            "range": "stddev: 0.001607464937901934",
            "extra": "mean: 4.569398834000026 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 272.13796444710493,
            "unit": "iter/sec",
            "range": "stddev: 0.0009573967955760463",
            "extra": "mean: 3.674606745999853 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 364.5088597308382,
            "unit": "iter/sec",
            "range": "stddev: 0.0007044478749762707",
            "extra": "mean: 2.743417542000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 10.618632825188664,
            "unit": "iter/sec",
            "range": "stddev: 0.01570914694013533",
            "extra": "mean: 94.17408214999963 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 434.0599984433344,
            "unit": "iter/sec",
            "range": "stddev: 0.05005529478999613",
            "extra": "mean: 2.303828971999934 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 539.798068430512,
            "unit": "iter/sec",
            "range": "stddev: 0.039849770338669224",
            "extra": "mean: 1.8525446059996966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 348.4562585252772,
            "unit": "iter/sec",
            "range": "stddev: 0.0008091657563472495",
            "extra": "mean: 2.869800657999832 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 11.105068438902205,
            "unit": "iter/sec",
            "range": "stddev: 0.0126615409313506",
            "extra": "mean: 90.04897227800024 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4025.937148379294,
            "unit": "iter/sec",
            "range": "stddev: 0.0001298397584804028",
            "extra": "mean: 248.38937200064493 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7212.183639909185,
            "unit": "iter/sec",
            "range": "stddev: 0.0000404110212304294",
            "extra": "mean: 138.65426199998865 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 8588.1196555567,
            "unit": "iter/sec",
            "range": "stddev: 0.00003515549947093432",
            "extra": "mean: 116.4399240004741 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 7942.472481244233,
            "unit": "iter/sec",
            "range": "stddev: 0.000032887378343196296",
            "extra": "mean: 125.90537799928825 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 253.8535603830872,
            "unit": "iter/sec",
            "range": "stddev: 0.0010019243485464033",
            "extra": "mean: 3.9392790019998642 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "164bfbaf9f56271092b4d364f6d1da066977e6b7",
          "message": "Merge pull request #709 from simphony/merge_master_into_dev\n\nPrepare for release: merge master into dev.",
          "timestamp": "2021-10-15T08:50:41+02:00",
          "tree_id": "9383ed3c2fbc9d4d41693743878bb146ad7cd2d8",
          "url": "https://github.com/simphony/osp-core/commit/164bfbaf9f56271092b4d364f6d1da066977e6b7"
        },
        "date": 1634280790881,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 263.05786449174246,
            "unit": "iter/sec",
            "range": "stddev: 0.006802984071108547",
            "extra": "mean: 3.8014449859999933 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 124.71529201197407,
            "unit": "iter/sec",
            "range": "stddev: 0.004766056598880861",
            "extra": "mean: 8.018262907999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 125.1161550858264,
            "unit": "iter/sec",
            "range": "stddev: 0.00548524024088585",
            "extra": "mean: 7.992572975999991 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 238.76418621709865,
            "unit": "iter/sec",
            "range": "stddev: 0.001729873214794703",
            "extra": "mean: 4.188232816000053 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 295.2668503036786,
            "unit": "iter/sec",
            "range": "stddev: 0.0013872853108384806",
            "extra": "mean: 3.386766915999921 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 581.3626384007191,
            "unit": "iter/sec",
            "range": "stddev: 0.0002697417745601437",
            "extra": "mean: 1.7200967760001191 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 16.63123738282302,
            "unit": "iter/sec",
            "range": "stddev: 0.015147904827700637",
            "extra": "mean: 60.127817129999855 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 436.9255957655697,
            "unit": "iter/sec",
            "range": "stddev: 0.04960178563413755",
            "extra": "mean: 2.2887191999997754 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 685.3577289433489,
            "unit": "iter/sec",
            "range": "stddev: 0.03087630559488766",
            "extra": "mean: 1.4590920299997947 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 598.8853046042258,
            "unit": "iter/sec",
            "range": "stddev: 0.00022793233275144678",
            "extra": "mean: 1.6697688060000928 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 21.747795915927806,
            "unit": "iter/sec",
            "range": "stddev: 0.008154759289717173",
            "extra": "mean: 45.98167114799955 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7426.988690587322,
            "unit": "iter/sec",
            "range": "stddev: 0.00007267993572822835",
            "extra": "mean: 134.64407200018513 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9751.639396863588,
            "unit": "iter/sec",
            "range": "stddev: 0.000020035442749893643",
            "extra": "mean: 102.54685999993285 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 17258.739221431653,
            "unit": "iter/sec",
            "range": "stddev: 0.000015250587666773037",
            "extra": "mean: 57.94166000018208 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14836.040243084291,
            "unit": "iter/sec",
            "range": "stddev: 0.000018438571297150072",
            "extra": "mean: 67.40342999987092 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 507.3809060645413,
            "unit": "iter/sec",
            "range": "stddev: 0.0005528457066410992",
            "extra": "mean: 1.9709058580000944 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "7b4000209bb0aeabac22217343bad3998b21cbcb",
          "message": "Remove packages from `setup_requires` as the setup only requires `os`, `setuptools`, and modules included in the package itself. (#711)\n\n* Remove packages from `setup_requires` as the setup only requires `os`, `setuptools`, and modules included in the package itself.\r\n\r\n* Remove `setup_requires` parameter.",
          "timestamp": "2021-10-19T09:19:59+02:00",
          "tree_id": "65a21324a3ea9064a52340d83214a79d3ed341fa",
          "url": "https://github.com/simphony/osp-core/commit/7b4000209bb0aeabac22217343bad3998b21cbcb"
        },
        "date": 1634628195987,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 265.60945772977595,
            "unit": "iter/sec",
            "range": "stddev: 0.005878905701575975",
            "extra": "mean: 3.7649261760000035 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 153.60672906988813,
            "unit": "iter/sec",
            "range": "stddev: 0.0031172612508623427",
            "extra": "mean: 6.510131463999986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 146.53466403673417,
            "unit": "iter/sec",
            "range": "stddev: 0.0035106093744788677",
            "extra": "mean: 6.824323832000012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 277.14693407878053,
            "unit": "iter/sec",
            "range": "stddev: 0.0010627740329946947",
            "extra": "mean: 3.6081943440000117 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 361.5266453181568,
            "unit": "iter/sec",
            "range": "stddev: 0.0009106169897095788",
            "extra": "mean: 2.7660478499999996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 528.3832742464327,
            "unit": "iter/sec",
            "range": "stddev: 0.00039788320743744604",
            "extra": "mean: 1.8925655839999393 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 21.50620576953016,
            "unit": "iter/sec",
            "range": "stddev: 0.007306975442516702",
            "extra": "mean: 46.49820664400008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 505.87462130820893,
            "unit": "iter/sec",
            "range": "stddev: 0.04275954642688003",
            "extra": "mean: 1.9767743979999752 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 859.4102805375226,
            "unit": "iter/sec",
            "range": "stddev: 0.024493120490925422",
            "extra": "mean: 1.163588594000231 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 589.5141667316257,
            "unit": "iter/sec",
            "range": "stddev: 0.0002395102908306377",
            "extra": "mean: 1.6963120760001118 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.367731436105814,
            "unit": "iter/sec",
            "range": "stddev: 0.006658596912751217",
            "extra": "mean: 44.707260673999684 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7901.403630639957,
            "unit": "iter/sec",
            "range": "stddev: 0.00006554345094014916",
            "extra": "mean: 126.55979199976741 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9945.906403136369,
            "unit": "iter/sec",
            "range": "stddev: 0.00002008389799930892",
            "extra": "mean: 100.5438780003658 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16712.574995911607,
            "unit": "iter/sec",
            "range": "stddev: 0.00001622094493128321",
            "extra": "mean: 59.83518400034882 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 15078.324962199145,
            "unit": "iter/sec",
            "range": "stddev: 0.000017056249487159153",
            "extra": "mean: 66.32036399977892 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 553.6075287646394,
            "unit": "iter/sec",
            "range": "stddev: 0.0003264537910682764",
            "extra": "mean: 1.806333816000432 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "a47e049ee4c41025515f9afb1ba0a761663ea342",
          "message": "Silence `rdflib_jsonld` deprecation warnings. (#710)",
          "timestamp": "2021-10-19T09:33:57+02:00",
          "tree_id": "b54111360c596be63ce60b4fcc8c12b58d80795c",
          "url": "https://github.com/simphony/osp-core/commit/a47e049ee4c41025515f9afb1ba0a761663ea342"
        },
        "date": 1634629042823,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 250.43456833774948,
            "unit": "iter/sec",
            "range": "stddev: 0.005857208334011325",
            "extra": "mean: 3.993058972000009 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 142.34583584206322,
            "unit": "iter/sec",
            "range": "stddev: 0.0032001125059960994",
            "extra": "mean: 7.02514403800002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 140.65919092624063,
            "unit": "iter/sec",
            "range": "stddev: 0.0037227270204397457",
            "extra": "mean: 7.109382568000008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 254.6935599063599,
            "unit": "iter/sec",
            "range": "stddev: 0.0013565941703419298",
            "extra": "mean: 3.926286948000012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 301.21875445511193,
            "unit": "iter/sec",
            "range": "stddev: 0.0011657127075330562",
            "extra": "mean: 3.3198464079998757 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 501.73913722875955,
            "unit": "iter/sec",
            "range": "stddev: 0.0004400376741270708",
            "extra": "mean: 1.9930675640000288 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 22.58956609879981,
            "unit": "iter/sec",
            "range": "stddev: 0.004974519748391953",
            "extra": "mean: 44.26822523399997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 406.07956399075533,
            "unit": "iter/sec",
            "range": "stddev: 0.05350487376723678",
            "extra": "mean: 2.4625715960007426 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 569.7396047410583,
            "unit": "iter/sec",
            "range": "stddev: 0.0373857361154444",
            "extra": "mean: 1.755187794000193 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 545.5003381250837,
            "unit": "iter/sec",
            "range": "stddev: 0.000287230938783578",
            "extra": "mean: 1.8331794320000938 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 21.475089563444786,
            "unit": "iter/sec",
            "range": "stddev: 0.006681565643256068",
            "extra": "mean: 46.56557995000006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6103.129038875714,
            "unit": "iter/sec",
            "range": "stddev: 0.00010406972337897096",
            "extra": "mean: 163.85037799958013 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8497.558710832447,
            "unit": "iter/sec",
            "range": "stddev: 0.000042801702096055806",
            "extra": "mean: 117.68085800045469 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15456.818703000203,
            "unit": "iter/sec",
            "range": "stddev: 0.000024728863290524154",
            "extra": "mean: 64.69636599967998 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12445.169074077856,
            "unit": "iter/sec",
            "range": "stddev: 0.00003565336827745417",
            "extra": "mean: 80.3524640001001 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 480.57556574763345,
            "unit": "iter/sec",
            "range": "stddev: 0.00047761609172611774",
            "extra": "mean: 2.0808382099999108 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f9954fba9a9205f6c081efd1390ba36ad49a9985",
          "message": "Bump package version to 3.5.8. (#712)",
          "timestamp": "2021-10-19T11:30:51+02:00",
          "tree_id": "d53b49dcda813257cb023ab12600a574a98f288d",
          "url": "https://github.com/simphony/osp-core/commit/f9954fba9a9205f6c081efd1390ba36ad49a9985"
        },
        "date": 1634635992636,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 234.28143136410878,
            "unit": "iter/sec",
            "range": "stddev: 0.007318196397015437",
            "extra": "mean: 4.268370712 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.88078872842867,
            "unit": "iter/sec",
            "range": "stddev: 0.003736461019069684",
            "extra": "mean: 7.944023945999966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 148.00517593755316,
            "unit": "iter/sec",
            "range": "stddev: 0.003294815174792589",
            "extra": "mean: 6.756520464000012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 246.08278955907306,
            "unit": "iter/sec",
            "range": "stddev: 0.0015697702947021414",
            "extra": "mean: 4.063673049999892 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 368.6675541974142,
            "unit": "iter/sec",
            "range": "stddev: 0.0008056257400174263",
            "extra": "mean: 2.7124708660001033 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 495.2865005217165,
            "unit": "iter/sec",
            "range": "stddev: 0.00047181863888834093",
            "extra": "mean: 2.0190334260001777 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 22.531709293127445,
            "unit": "iter/sec",
            "range": "stddev: 0.006106164575594607",
            "extra": "mean: 44.38189695199986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 462.24519760817117,
            "unit": "iter/sec",
            "range": "stddev: 0.04687539706934746",
            "extra": "mean: 2.163354006000219 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 839.1011482042943,
            "unit": "iter/sec",
            "range": "stddev: 0.025087003611518152",
            "extra": "mean: 1.1917514380000966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 537.3730326703891,
            "unit": "iter/sec",
            "range": "stddev: 0.0004116965118497784",
            "extra": "mean: 1.8609046959998352 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.764965796625503,
            "unit": "iter/sec",
            "range": "stddev: 0.00469432319523353",
            "extra": "mean: 43.92714704400004 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6776.748714935425,
            "unit": "iter/sec",
            "range": "stddev: 0.00007600130464065784",
            "extra": "mean: 147.56338799992363 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 5828.247740351089,
            "unit": "iter/sec",
            "range": "stddev: 0.00008739330239645393",
            "extra": "mean: 171.5781559998959 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 11068.496171041996,
            "unit": "iter/sec",
            "range": "stddev: 0.000024732628898091684",
            "extra": "mean: 90.34650999981864 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12509.754794008562,
            "unit": "iter/sec",
            "range": "stddev: 0.00003303972858872232",
            "extra": "mean: 79.9376180002298 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 526.151952955541,
            "unit": "iter/sec",
            "range": "stddev: 0.0003996430441727182",
            "extra": "mean: 1.9005916339998805 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "50434de02d7ba655119f6d5f3d235562ef70bea7",
          "message": "Get foaf ontology from official website again (#715)\n\n* Revert \"Get FOAF ontology from web archive (#702)\"\r\n\r\nThis reverts commit 6f92f04b0beac92fd2cc3b307c9ec9286ef290bb.",
          "timestamp": "2021-10-19T15:08:48+02:00",
          "tree_id": "e42e95989481ff21fb8aebd18aa6da4d1a84da2f",
          "url": "https://github.com/simphony/osp-core/commit/50434de02d7ba655119f6d5f3d235562ef70bea7"
        },
        "date": 1634649083126,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 255.8088414282811,
            "unit": "iter/sec",
            "range": "stddev: 0.0063111497715343376",
            "extra": "mean: 3.9091690280000013 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 125.84746187361728,
            "unit": "iter/sec",
            "range": "stddev: 0.003492174099369408",
            "extra": "mean: 7.946127678000001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 130.40097547545085,
            "unit": "iter/sec",
            "range": "stddev: 0.003793442314898324",
            "extra": "mean: 7.668654289999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 257.759439639388,
            "unit": "iter/sec",
            "range": "stddev: 0.0014204661554421503",
            "extra": "mean: 3.8795863360000524 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 359.2413361554964,
            "unit": "iter/sec",
            "range": "stddev: 0.0008225685291037894",
            "extra": "mean: 2.783644028000033 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 531.7832048607969,
            "unit": "iter/sec",
            "range": "stddev: 0.0003672997135416349",
            "extra": "mean: 1.8804655559999617 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 18.841749908480526,
            "unit": "iter/sec",
            "range": "stddev: 0.011060533692926231",
            "extra": "mean: 53.073626645999994 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 453.8552413966726,
            "unit": "iter/sec",
            "range": "stddev: 0.04756871910839429",
            "extra": "mean: 2.203345711999816 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 779.8425061268945,
            "unit": "iter/sec",
            "range": "stddev: 0.026852603894410687",
            "extra": "mean: 1.2823101999998983 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 485.2575792214128,
            "unit": "iter/sec",
            "range": "stddev: 0.00047126536456042987",
            "extra": "mean: 2.0607612179998966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 20.063197885598314,
            "unit": "iter/sec",
            "range": "stddev: 0.010254655388824857",
            "extra": "mean: 49.84250296000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6334.180787591028,
            "unit": "iter/sec",
            "range": "stddev: 0.00009451312413636655",
            "extra": "mean: 157.8736120003157 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9269.652599741186,
            "unit": "iter/sec",
            "range": "stddev: 0.00002530549765709668",
            "extra": "mean: 107.87890800006039 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15992.999927858937,
            "unit": "iter/sec",
            "range": "stddev: 0.000023886746217048464",
            "extra": "mean: 62.52735600017446 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 13625.9147894345,
            "unit": "iter/sec",
            "range": "stddev: 0.00002323147530719698",
            "extra": "mean: 73.3895679998966 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 521.4848373777862,
            "unit": "iter/sec",
            "range": "stddev: 0.0003328620363402168",
            "extra": "mean: 1.917601296000015 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "8adc93b8957eb93e82e8363565bed140fa1b36f8",
          "message": "Merge pull request #713 from simphony/dev\n\nMerge sprint 5.",
          "timestamp": "2021-10-19T15:54:28+02:00",
          "tree_id": "e42e95989481ff21fb8aebd18aa6da4d1a84da2f",
          "url": "https://github.com/simphony/osp-core/commit/8adc93b8957eb93e82e8363565bed140fa1b36f8"
        },
        "date": 1634651801739,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 200.6174525311959,
            "unit": "iter/sec",
            "range": "stddev: 0.008342388022152984",
            "extra": "mean: 4.984611196000011 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 104.94430138188861,
            "unit": "iter/sec",
            "range": "stddev: 0.004749900014884697",
            "extra": "mean: 9.528864234000046 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 115.31971633125667,
            "unit": "iter/sec",
            "range": "stddev: 0.005096823432205568",
            "extra": "mean: 8.67154405000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 275.2488209705683,
            "unit": "iter/sec",
            "range": "stddev: 0.001311757389538995",
            "extra": "mean: 3.6330764160000797 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 338.55243097647957,
            "unit": "iter/sec",
            "range": "stddev: 0.0009479084439950476",
            "extra": "mean: 2.953752235999964 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 556.0561797303526,
            "unit": "iter/sec",
            "range": "stddev: 0.000281609541591129",
            "extra": "mean: 1.7983794380001825 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 21.753903157625416,
            "unit": "iter/sec",
            "range": "stddev: 0.007817915472644068",
            "extra": "mean: 45.968762145999946 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 407.99549589296277,
            "unit": "iter/sec",
            "range": "stddev: 0.052806481031724674",
            "extra": "mean: 2.4510074499997643 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 800.3714991543585,
            "unit": "iter/sec",
            "range": "stddev: 0.026264414129278886",
            "extra": "mean: 1.2494198020001477 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 561.9518362141272,
            "unit": "iter/sec",
            "range": "stddev: 0.0002457048843274868",
            "extra": "mean: 1.7795119359997216 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 21.013310876185095,
            "unit": "iter/sec",
            "range": "stddev: 0.010209364714486429",
            "extra": "mean: 47.58888334599973 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7542.951678891762,
            "unit": "iter/sec",
            "range": "stddev: 0.00006519675449406342",
            "extra": "mean: 132.57409599989955 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9863.06573238245,
            "unit": "iter/sec",
            "range": "stddev: 0.000019744398596487803",
            "extra": "mean: 101.3883539999938 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14049.371345396281,
            "unit": "iter/sec",
            "range": "stddev: 0.00003693505551178608",
            "extra": "mean: 71.17756200014469 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14422.549251976527,
            "unit": "iter/sec",
            "range": "stddev: 0.000022117237996065237",
            "extra": "mean: 69.3358699997475 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 543.8136100342895,
            "unit": "iter/sec",
            "range": "stddev: 0.00030263313687921956",
            "extra": "mean: 1.8388653420000765 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "45dba6e41251b6624311c8d254792b2c4ecf6344",
          "message": "Fix Dockerfile (`dev`) (#723)\n\n* Docker image now builds (failing previously).\r\n\r\n* Changed deprecated `MAINTAINER` to `LABEL org.opencontainers.image.authors`.\r\n\r\n* Do not run tox when building the docker image, as GitHub's CI is already testing every commit.\r\n\r\n* Fix little detail in `tox.ini`.",
          "timestamp": "2021-11-12T13:20:31+01:00",
          "tree_id": "875d6e5520d8acfb414ce2eca2326855f335ba2d",
          "url": "https://github.com/simphony/osp-core/commit/45dba6e41251b6624311c8d254792b2c4ecf6344"
        },
        "date": 1636719769627,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 242.98379268847486,
            "unit": "iter/sec",
            "range": "stddev: 0.0062436999227540365",
            "extra": "mean: 4.115500828000005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 107.76632914085695,
            "unit": "iter/sec",
            "range": "stddev: 0.004955261809947514",
            "extra": "mean: 9.279336208000005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 110.79902391901156,
            "unit": "iter/sec",
            "range": "stddev: 0.004322881750608497",
            "extra": "mean: 9.025350266000078 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 220.17653143961337,
            "unit": "iter/sec",
            "range": "stddev: 0.0020563186022675255",
            "extra": "mean: 4.54181012600003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 357.31655152604657,
            "unit": "iter/sec",
            "range": "stddev: 0.0009691681955685996",
            "extra": "mean: 2.7986388979999575 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 534.7916185206999,
            "unit": "iter/sec",
            "range": "stddev: 0.0004850458436887579",
            "extra": "mean: 1.8698871960000503 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 23.00720279853535,
            "unit": "iter/sec",
            "range": "stddev: 0.007408760242680093",
            "extra": "mean: 43.46464925599997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 456.94309102352116,
            "unit": "iter/sec",
            "range": "stddev: 0.04605313411432455",
            "extra": "mean: 2.188456329999582 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 840.8142581826841,
            "unit": "iter/sec",
            "range": "stddev: 0.024880715551679124",
            "extra": "mean: 1.1893233139996653 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 495.55610017606534,
            "unit": "iter/sec",
            "range": "stddev: 0.0005727706780044492",
            "extra": "mean: 2.0179350020002005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 24.153080804391347,
            "unit": "iter/sec",
            "range": "stddev: 0.005178171999806048",
            "extra": "mean: 41.40258578599989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7778.632321007918,
            "unit": "iter/sec",
            "range": "stddev: 0.00006706447340644341",
            "extra": "mean: 128.55730400050902 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9967.532358151851,
            "unit": "iter/sec",
            "range": "stddev: 0.000018409855233892663",
            "extra": "mean: 100.32573399996636 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14316.638224339364,
            "unit": "iter/sec",
            "range": "stddev: 0.00002791387400398828",
            "extra": "mean: 69.84879999970417 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 11404.726036358054,
            "unit": "iter/sec",
            "range": "stddev: 0.0000273572348456714",
            "extra": "mean: 87.68294799997989 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 549.8033322691136,
            "unit": "iter/sec",
            "range": "stddev: 0.00025186956764602523",
            "extra": "mean: 1.8188321920001158 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "2c3fbbf770ecd5bc0a324aebc824e63f9a66b236",
          "message": "Fix Dockerfile (`master`) (#724)\n\n* Docker image now builds (failing previously).\r\n\r\n* Changed deprecated `MAINTAINER` to `LABEL org.opencontainers.image.authors`.\r\n\r\n* Do not run tox when building the docker image, as GitHub's CI is already testing every commit.\r\n\r\n* Fix little detail in `tox.ini`.",
          "timestamp": "2021-11-12T13:21:48+01:00",
          "tree_id": "875d6e5520d8acfb414ce2eca2326855f335ba2d",
          "url": "https://github.com/simphony/osp-core/commit/2c3fbbf770ecd5bc0a324aebc824e63f9a66b236"
        },
        "date": 1636719856101,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 251.0081423256166,
            "unit": "iter/sec",
            "range": "stddev: 0.006426947369913148",
            "extra": "mean: 3.983934508000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 151.10898156245483,
            "unit": "iter/sec",
            "range": "stddev: 0.003462855651471909",
            "extra": "mean: 6.61774032000004 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 160.864596501675,
            "unit": "iter/sec",
            "range": "stddev: 0.002778771606396935",
            "extra": "mean: 6.216408220000027 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 264.80281175548396,
            "unit": "iter/sec",
            "range": "stddev: 0.0014292217087396827",
            "extra": "mean: 3.7763949460000035 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 359.86073542120886,
            "unit": "iter/sec",
            "range": "stddev: 0.0008268726385560748",
            "extra": "mean: 2.778852765999943 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 570.9793744503938,
            "unit": "iter/sec",
            "range": "stddev: 0.0003624743888654784",
            "extra": "mean: 1.7513767479999913 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 22.165984672967333,
            "unit": "iter/sec",
            "range": "stddev: 0.008824936885541777",
            "extra": "mean: 45.114169966000034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 458.4461809686064,
            "unit": "iter/sec",
            "range": "stddev: 0.04711982584021464",
            "extra": "mean: 2.1812811220003994 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 655.2483594277907,
            "unit": "iter/sec",
            "range": "stddev: 0.032401955959921645",
            "extra": "mean: 1.526138884000062 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 426.3219453336668,
            "unit": "iter/sec",
            "range": "stddev: 0.0006730194096582661",
            "extra": "mean: 2.3456451420002224 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 17.878603743721378,
            "unit": "iter/sec",
            "range": "stddev: 0.011856677847182272",
            "extra": "mean: 55.932779446000126 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5374.267942750108,
            "unit": "iter/sec",
            "range": "stddev: 0.00011023911365277582",
            "extra": "mean: 186.0718539999482 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7099.829135511983,
            "unit": "iter/sec",
            "range": "stddev: 0.0000589227993301494",
            "extra": "mean: 140.84846000000084 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16409.72860608922,
            "unit": "iter/sec",
            "range": "stddev: 0.00002155183347808617",
            "extra": "mean: 60.93945999990069 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12736.683561705873,
            "unit": "iter/sec",
            "range": "stddev: 0.00002663206012257116",
            "extra": "mean: 78.51337400001057 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 311.1738114447383,
            "unit": "iter/sec",
            "range": "stddev: 0.0008481431991753335",
            "extra": "mean: 3.2136380480000355 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "2c3fbbf770ecd5bc0a324aebc824e63f9a66b236",
          "message": "Fix Dockerfile (`master`) (#724)\n\n* Docker image now builds (failing previously).\r\n\r\n* Changed deprecated `MAINTAINER` to `LABEL org.opencontainers.image.authors`.\r\n\r\n* Do not run tox when building the docker image, as GitHub's CI is already testing every commit.\r\n\r\n* Fix little detail in `tox.ini`.",
          "timestamp": "2021-11-12T13:21:48+01:00",
          "tree_id": "875d6e5520d8acfb414ce2eca2326855f335ba2d",
          "url": "https://github.com/simphony/osp-core/commit/2c3fbbf770ecd5bc0a324aebc824e63f9a66b236"
        },
        "date": 1636720042439,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 229.15318612896556,
            "unit": "iter/sec",
            "range": "stddev: 0.006549360070202573",
            "extra": "mean: 4.363893065999999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 132.27509483218265,
            "unit": "iter/sec",
            "range": "stddev: 0.004489683835819189",
            "extra": "mean: 7.5600021399999715 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 113.25260325214211,
            "unit": "iter/sec",
            "range": "stddev: 0.004613700847860736",
            "extra": "mean: 8.82981910599998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 204.1534347493048,
            "unit": "iter/sec",
            "range": "stddev: 0.0022736991943949525",
            "extra": "mean: 4.898276638000112 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 234.206200089684,
            "unit": "iter/sec",
            "range": "stddev: 0.0016582718147348783",
            "extra": "mean: 4.269741789999891 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 378.26798325976756,
            "unit": "iter/sec",
            "range": "stddev: 0.0007411046794120412",
            "extra": "mean: 2.6436284439999014 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 19.094669030797952,
            "unit": "iter/sec",
            "range": "stddev: 0.013356082733987286",
            "extra": "mean: 52.370638023999874 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 489.22729662926474,
            "unit": "iter/sec",
            "range": "stddev: 0.04407549554509833",
            "extra": "mean: 2.0440396659996622 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 864.8944085354096,
            "unit": "iter/sec",
            "range": "stddev: 0.024309101458393698",
            "extra": "mean: 1.156210504000569 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 555.0692273348205,
            "unit": "iter/sec",
            "range": "stddev: 0.0004260564571173627",
            "extra": "mean: 1.8015770840000016 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.031768113173214,
            "unit": "iter/sec",
            "range": "stddev: 0.009264158467168587",
            "extra": "mean: 45.38900349999966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6919.513724809987,
            "unit": "iter/sec",
            "range": "stddev: 0.00007591771785890813",
            "extra": "mean: 144.51882599993837 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8367.290867691163,
            "unit": "iter/sec",
            "range": "stddev: 0.000046734408685620614",
            "extra": "mean: 119.51299599985532 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 15496.200904845777,
            "unit": "iter/sec",
            "range": "stddev: 0.000022462388807859446",
            "extra": "mean: 64.53194600021561 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12990.665894791075,
            "unit": "iter/sec",
            "range": "stddev: 0.00002807115190183139",
            "extra": "mean: 76.9783479999262 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 534.9859090863349,
            "unit": "iter/sec",
            "range": "stddev: 0.0002947300190760051",
            "extra": "mean: 1.8692081100001872 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "89aff8d131fcad55cde34fabf6c82fd6fbd3691f",
          "message": "Bump package version to 3.5.9. (#729)",
          "timestamp": "2021-11-17T15:04:06+01:00",
          "tree_id": "6a04f262b79ce635cedc3117b624e45f9d0bedb7",
          "url": "https://github.com/simphony/osp-core/commit/89aff8d131fcad55cde34fabf6c82fd6fbd3691f"
        },
        "date": 1637157975311,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 270.1753189799237,
            "unit": "iter/sec",
            "range": "stddev: 0.006098298576976448",
            "extra": "mean: 3.70130034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 155.078135543254,
            "unit": "iter/sec",
            "range": "stddev: 0.0033588213694687673",
            "extra": "mean: 6.448362281999982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 158.22450791180412,
            "unit": "iter/sec",
            "range": "stddev: 0.0030551382462141504",
            "extra": "mean: 6.320133418000008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 276.3056003556554,
            "unit": "iter/sec",
            "range": "stddev: 0.0013671953594809377",
            "extra": "mean: 3.6191810759999754 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 362.6800607217819,
            "unit": "iter/sec",
            "range": "stddev: 0.0009180456106400612",
            "extra": "mean: 2.7572511099999986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 519.8571163982135,
            "unit": "iter/sec",
            "range": "stddev: 0.0005585916555854213",
            "extra": "mean: 1.9236054839999426 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 20.016990751630047,
            "unit": "iter/sec",
            "range": "stddev: 0.010747739770648709",
            "extra": "mean: 49.95755917599986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 512.654075862712,
            "unit": "iter/sec",
            "range": "stddev: 0.042110087414932496",
            "extra": "mean: 1.9506330820001097 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 848.0772898831987,
            "unit": "iter/sec",
            "range": "stddev: 0.02476844025987248",
            "extra": "mean: 1.1791378120002776 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 546.8267844028423,
            "unit": "iter/sec",
            "range": "stddev: 0.0002981423288800074",
            "extra": "mean: 1.828732659999531 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 21.116714290423,
            "unit": "iter/sec",
            "range": "stddev: 0.007897165020150356",
            "extra": "mean: 47.35585215800012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5814.256167728486,
            "unit": "iter/sec",
            "range": "stddev: 0.00014778269857909624",
            "extra": "mean: 171.9910460000733 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7791.351957731386,
            "unit": "iter/sec",
            "range": "stddev: 0.00005155888917349741",
            "extra": "mean: 128.34742999996251 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 16074.91321063829,
            "unit": "iter/sec",
            "range": "stddev: 0.000022057475020814332",
            "extra": "mean: 62.20873400039295 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 13845.521254927875,
            "unit": "iter/sec",
            "range": "stddev: 0.00002539624629974001",
            "extra": "mean: 72.22552200005339 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 459.92059757863524,
            "unit": "iter/sec",
            "range": "stddev: 0.0006233632755013391",
            "extra": "mean: 2.17428835600046 msec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "1113c9d09236573d94de7c3fafb30347573afba1",
          "message": "Performance improvements (#730)\n\nModerate, but easy performance improvements (see PR for details).",
          "timestamp": "2021-11-30T16:25:19+01:00",
          "tree_id": "de56ebaa3872973ca03193395429efad614a828d",
          "url": "https://github.com/simphony/osp-core/commit/1113c9d09236573d94de7c3fafb30347573afba1"
        },
        "date": 1638286028467,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 393.0006749566513,
            "unit": "iter/sec",
            "range": "stddev: 0.008824068826162008",
            "extra": "mean: 2.544524891999999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 823.259893715545,
            "unit": "iter/sec",
            "range": "stddev: 0.00031068547736060075",
            "extra": "mean: 1.214683245999984 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 782.5900240069145,
            "unit": "iter/sec",
            "range": "stddev: 0.00013895280097725435",
            "extra": "mean: 1.277808264000008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 161.54708859786865,
            "unit": "iter/sec",
            "range": "stddev: 0.0016603938562080472",
            "extra": "mean: 6.190145601999994 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 254.95112782937107,
            "unit": "iter/sec",
            "range": "stddev: 0.0012098436317732378",
            "extra": "mean: 3.9223203619999727 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 530.2383588978596,
            "unit": "iter/sec",
            "range": "stddev: 0.0005402522983093063",
            "extra": "mean: 1.8859442799999897 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 19.12920495810402,
            "unit": "iter/sec",
            "range": "stddev: 0.01344071541958259",
            "extra": "mean: 52.27608790800025 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 6994.949730229434,
            "unit": "iter/sec",
            "range": "stddev: 0.0009029929408379947",
            "extra": "mean: 142.96028400009675 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 11727.05706242331,
            "unit": "iter/sec",
            "range": "stddev: 0.0003541272628415922",
            "extra": "mean: 85.27288600004113 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 572.0163505884803,
            "unit": "iter/sec",
            "range": "stddev: 0.00045989838920742327",
            "extra": "mean: 1.7482017760003146 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 18.67285633124054,
            "unit": "iter/sec",
            "range": "stddev: 0.01487123829212378",
            "extra": "mean: 53.553670753999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 4244.014538985611,
            "unit": "iter/sec",
            "range": "stddev: 0.00012089679083529166",
            "extra": "mean: 235.6259599994246 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 5425.603784507012,
            "unit": "iter/sec",
            "range": "stddev: 0.000038975395012847524",
            "extra": "mean: 184.3112840004153 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 8599.242551199095,
            "unit": "iter/sec",
            "range": "stddev: 0.00003332663353960606",
            "extra": "mean: 116.28931199999215 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 7551.310437024969,
            "unit": "iter/sec",
            "range": "stddev: 0.00003350262644558695",
            "extra": "mean: 132.42734600035533 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 1393.5488310187498,
            "unit": "iter/sec",
            "range": "stddev: 0.00013842343351183275",
            "extra": "mean: 717.59236399987 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "d117e5f0cfafe2bd2a34e7f240d5ed7371dee695",
          "message": "Bump package version to 3.6.0 (#735)",
          "timestamp": "2021-12-09T10:18:57+01:00",
          "tree_id": "898cc0a1a032b6ae40beeda7d26ca86ac90bdb53",
          "url": "https://github.com/simphony/osp-core/commit/d117e5f0cfafe2bd2a34e7f240d5ed7371dee695"
        },
        "date": 1639041638362,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 315.1919180485423,
            "unit": "iter/sec",
            "range": "stddev: 0.00651705812691546",
            "extra": "mean: 3.172670182000007 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1118.5734001209455,
            "unit": "iter/sec",
            "range": "stddev: 0.00020958213863574295",
            "extra": "mean: 893.9958700000154 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 932.5057660468198,
            "unit": "iter/sec",
            "range": "stddev: 0.0004031348674084652",
            "extra": "mean: 1.0723794280000103 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 145.3144404786333,
            "unit": "iter/sec",
            "range": "stddev: 0.0019300754166601418",
            "extra": "mean: 6.881628533999949 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 280.34617093603435,
            "unit": "iter/sec",
            "range": "stddev: 0.0008082783070755656",
            "extra": "mean: 3.567018578000006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 512.2643450567754,
            "unit": "iter/sec",
            "range": "stddev: 0.0005523430293692048",
            "extra": "mean: 1.952117124000047 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 18.418342996885702,
            "unit": "iter/sec",
            "range": "stddev: 0.012766140081599141",
            "extra": "mean: 54.29370058800006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 11481.301964945611,
            "unit": "iter/sec",
            "range": "stddev: 0.0004591090917762033",
            "extra": "mean: 87.09813600000871 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 11796.264915607188,
            "unit": "iter/sec",
            "range": "stddev: 0.00035391904981265786",
            "extra": "mean: 84.77259600002185 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 534.9446516734596,
            "unit": "iter/sec",
            "range": "stddev: 0.00046084578381635154",
            "extra": "mean: 1.8693522719999436 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 23.509476520747413,
            "unit": "iter/sec",
            "range": "stddev: 0.00575824627109671",
            "extra": "mean: 42.536038567999896 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7946.332630818168,
            "unit": "iter/sec",
            "range": "stddev: 0.00006050854843593826",
            "extra": "mean: 125.84421599993334 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7828.455493172016,
            "unit": "iter/sec",
            "range": "stddev: 0.000051387634461705485",
            "extra": "mean: 127.73911799999381 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14490.601873753812,
            "unit": "iter/sec",
            "range": "stddev: 0.000027780617355392",
            "extra": "mean: 69.01024600028904 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12657.235136330184,
            "unit": "iter/sec",
            "range": "stddev: 0.000025877593971864552",
            "extra": "mean: 79.00619600007985 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2579.396853032673,
            "unit": "iter/sec",
            "range": "stddev: 0.00009689814248249792",
            "extra": "mean: 387.6875319996884 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "a90024ddd724e72bcfea21bbb4a79566679e9e24",
          "message": "Merge branch 'master' into dev",
          "timestamp": "2021-12-09T10:27:12+01:00",
          "tree_id": "898cc0a1a032b6ae40beeda7d26ca86ac90bdb53",
          "url": "https://github.com/simphony/osp-core/commit/a90024ddd724e72bcfea21bbb4a79566679e9e24"
        },
        "date": 1639042630030,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 449.7005177130449,
            "unit": "iter/sec",
            "range": "stddev: 0.00603693930293148",
            "extra": "mean: 2.223702131999996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1013.1202558263107,
            "unit": "iter/sec",
            "range": "stddev: 0.00022102499534551164",
            "extra": "mean: 987.0496560000079 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1055.1521463870063,
            "unit": "iter/sec",
            "range": "stddev: 0.0003092984872877678",
            "extra": "mean: 947.730622000007 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 156.36488924896662,
            "unit": "iter/sec",
            "range": "stddev: 0.0015725923993969405",
            "extra": "mean: 6.395297594000047 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 263.73786262532053,
            "unit": "iter/sec",
            "range": "stddev: 0.0009044019757571138",
            "extra": "mean: 3.791643679999982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 440.2418596502132,
            "unit": "iter/sec",
            "range": "stddev: 0.0007412906041271123",
            "extra": "mean: 2.271478684000048 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 21.555452555757004,
            "unit": "iter/sec",
            "range": "stddev: 0.008313462079120154",
            "extra": "mean: 46.39197425400012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 10756.717198792228,
            "unit": "iter/sec",
            "range": "stddev: 0.0005333966941530781",
            "extra": "mean: 92.96516599992799 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 12118.961666759076,
            "unit": "iter/sec",
            "range": "stddev: 0.0003347296779703694",
            "extra": "mean: 82.51531999997042 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 539.06711219085,
            "unit": "iter/sec",
            "range": "stddev: 0.0005135139467693711",
            "extra": "mean: 1.8550565919999258 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 23.07266519759249,
            "unit": "iter/sec",
            "range": "stddev: 0.006496928238872509",
            "extra": "mean: 43.3413301600001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6175.811291315105,
            "unit": "iter/sec",
            "range": "stddev: 0.00009066840436662423",
            "extra": "mean: 161.92204600005766 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8450.445094210134,
            "unit": "iter/sec",
            "range": "stddev: 0.00003956806538333535",
            "extra": "mean: 118.33696200039867 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 14023.97246630798,
            "unit": "iter/sec",
            "range": "stddev: 0.00003269041994636986",
            "extra": "mean: 71.30647200017393 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 9861.258210932972,
            "unit": "iter/sec",
            "range": "stddev: 0.000054044559423234705",
            "extra": "mean: 101.40693800019562 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 1854.7448760408147,
            "unit": "iter/sec",
            "range": "stddev: 0.00012859080026039643",
            "extra": "mean: 539.1577099997846 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f1e47966a7f8d4361f1314c715eaaa3aa00a7a2a",
          "message": "Update `README.md` (#737)",
          "timestamp": "2021-12-09T10:46:44+01:00",
          "tree_id": "f858877b4dcad0bf1b2cf56b6d638e718495b635",
          "url": "https://github.com/simphony/osp-core/commit/f1e47966a7f8d4361f1314c715eaaa3aa00a7a2a"
        },
        "date": 1639043601482,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 399.37104236675896,
            "unit": "iter/sec",
            "range": "stddev: 0.007503567970710819",
            "extra": "mean: 2.503937176000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 900.6930534015864,
            "unit": "iter/sec",
            "range": "stddev: 0.0003255552212332825",
            "extra": "mean: 1.110256147999996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1110.352727860713,
            "unit": "iter/sec",
            "range": "stddev: 0.00025293680390762525",
            "extra": "mean: 900.6147100000135 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 134.47477733305925,
            "unit": "iter/sec",
            "range": "stddev: 0.0024526463239934442",
            "extra": "mean: 7.436338768000029 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 261.27835915701854,
            "unit": "iter/sec",
            "range": "stddev: 0.001027566041360154",
            "extra": "mean: 3.8273357320000514 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 453.35494035069354,
            "unit": "iter/sec",
            "range": "stddev: 0.0006580868847951287",
            "extra": "mean: 2.205777219999959 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 19.051562634717342,
            "unit": "iter/sec",
            "range": "stddev: 0.012194568115052292",
            "extra": "mean: 52.48913273800002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 11162.649560244356,
            "unit": "iter/sec",
            "range": "stddev: 0.0005033324566658063",
            "extra": "mean: 89.58446600003356 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 9947.47375745172,
            "unit": "iter/sec",
            "range": "stddev: 0.0003660482267943312",
            "extra": "mean: 100.52803600018478 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 414.77925204731474,
            "unit": "iter/sec",
            "range": "stddev: 0.004623930146960018",
            "extra": "mean: 2.4109209779999503 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 22.04141768960068,
            "unit": "iter/sec",
            "range": "stddev: 0.009201745834289163",
            "extra": "mean: 45.36913251600001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 5648.993038748309,
            "unit": "iter/sec",
            "range": "stddev: 0.00011310928230080096",
            "extra": "mean: 177.02269999992382 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 7704.978826343547,
            "unit": "iter/sec",
            "range": "stddev: 0.00005703878366138335",
            "extra": "mean: 129.78620999982127 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 11587.934799860112,
            "unit": "iter/sec",
            "range": "stddev: 0.00004255591660876649",
            "extra": "mean: 86.29665400016506 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 13655.703713006038,
            "unit": "iter/sec",
            "range": "stddev: 0.000030248587467719262",
            "extra": "mean: 73.22947399975988 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2037.3059984050572,
            "unit": "iter/sec",
            "range": "stddev: 0.00015914552854338484",
            "extra": "mean: 490.84428199930136 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "e1383f848a80add9ed32fee0244b7d55da84bdb2",
          "message": "Merge pull request #736 from simphony/dev\n\nMerge release 3.6.0.",
          "timestamp": "2021-12-09T10:57:41+01:00",
          "tree_id": "f858877b4dcad0bf1b2cf56b6d638e718495b635",
          "url": "https://github.com/simphony/osp-core/commit/e1383f848a80add9ed32fee0244b7d55da84bdb2"
        },
        "date": 1639043948584,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 459.954450306027,
            "unit": "iter/sec",
            "range": "stddev: 0.005686357958582121",
            "extra": "mean: 2.1741283279999966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1002.8697358179113,
            "unit": "iter/sec",
            "range": "stddev: 0.00023147083890432733",
            "extra": "mean: 997.1384760000053 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1176.228733466886,
            "unit": "iter/sec",
            "range": "stddev: 0.00020021372857945445",
            "extra": "mean: 850.1747760000225 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 182.98218144512296,
            "unit": "iter/sec",
            "range": "stddev: 0.0006060160010715713",
            "extra": "mean: 5.465012998000047 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 291.94168273841007,
            "unit": "iter/sec",
            "range": "stddev: 0.0005438914457343006",
            "extra": "mean: 3.4253416319999594 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 612.4968754237392,
            "unit": "iter/sec",
            "range": "stddev: 0.0002544349822168022",
            "extra": "mean: 1.6326613900000346 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 23.340640630953615,
            "unit": "iter/sec",
            "range": "stddev: 0.006484754920384864",
            "extra": "mean: 42.84372549200007 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 11990.545694534387,
            "unit": "iter/sec",
            "range": "stddev: 0.00045303821768645817",
            "extra": "mean: 83.39903999997489 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 12281.91826761238,
            "unit": "iter/sec",
            "range": "stddev: 0.0003298207374757757",
            "extra": "mean: 81.42050600002904 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 571.8235675435641,
            "unit": "iter/sec",
            "range": "stddev: 0.000259797287320795",
            "extra": "mean: 1.7487911600002661 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 23.326166542987103,
            "unit": "iter/sec",
            "range": "stddev: 0.007082400078437243",
            "extra": "mean: 42.870310394000214 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6652.41294059564,
            "unit": "iter/sec",
            "range": "stddev: 0.00007538533693996226",
            "extra": "mean: 150.32139600018013 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8581.346843040634,
            "unit": "iter/sec",
            "range": "stddev: 0.00004359352791494008",
            "extra": "mean: 116.5318240004467 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 17013.26718379685,
            "unit": "iter/sec",
            "range": "stddev: 0.00001563039270379281",
            "extra": "mean: 58.77765800047996 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 14926.291881031284,
            "unit": "iter/sec",
            "range": "stddev: 0.000016463392625965697",
            "extra": "mean: 66.99587599990764 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2756.639589737253,
            "unit": "iter/sec",
            "range": "stddev: 0.00006649290792033639",
            "extra": "mean: 362.76051600032133 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "45487f26c438f4cb552e777c1c31b907dd73581d",
          "message": "Require `websockets >= 10` for `python_version >= '3.10'` (dev) (#742)\n\n* Require `websockets >= 10` for `python_version >= '3.10'`.\r\n\r\n* Adapt `test_communication_engine.py` to the two possible ways of initializing the `ConnectionClosedOK` exception.",
          "timestamp": "2022-01-21T09:49:39+01:00",
          "tree_id": "0ac58ea62afb8018c40dad820cc06f8342dcab2b",
          "url": "https://github.com/simphony/osp-core/commit/45487f26c438f4cb552e777c1c31b907dd73581d"
        },
        "date": 1642755862133,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 492.5160210684239,
            "unit": "iter/sec",
            "range": "stddev: 0.005063096264839682",
            "extra": "mean: 2.0303908040000036 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1470.5465279995028,
            "unit": "iter/sec",
            "range": "stddev: 0.0001456267894532929",
            "extra": "mean: 680.0192859999994 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1671.0592687625967,
            "unit": "iter/sec",
            "range": "stddev: 0.00012703546223357952",
            "extra": "mean: 598.4228199999694 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 250.01901557125686,
            "unit": "iter/sec",
            "range": "stddev: 0.0010871348276058578",
            "extra": "mean: 3.999695774000015 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 494.17640044685584,
            "unit": "iter/sec",
            "range": "stddev: 0.00009649506953680932",
            "extra": "mean: 2.0235689100000656 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 963.1271471764087,
            "unit": "iter/sec",
            "range": "stddev: 0.00013946635038914525",
            "extra": "mean: 1.03828451199999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 41.4725765119717,
            "unit": "iter/sec",
            "range": "stddev: 0.0017500660460608786",
            "extra": "mean: 24.112319129999904 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17643.411203939784,
            "unit": "iter/sec",
            "range": "stddev: 0.0002859116369719744",
            "extra": "mean: 56.67838200000119 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 18335.794180280584,
            "unit": "iter/sec",
            "range": "stddev: 0.00023408112851902127",
            "extra": "mean: 54.53813399996932 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 962.8705132715284,
            "unit": "iter/sec",
            "range": "stddev: 0.00013153582812840337",
            "extra": "mean: 1.0385612460000644 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 41.14388830067193,
            "unit": "iter/sec",
            "range": "stddev: 0.002428915976696313",
            "extra": "mean: 24.304946404000148 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 12785.25371336273,
            "unit": "iter/sec",
            "range": "stddev: 0.00005150410720029409",
            "extra": "mean: 78.21510800015119 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 16289.74053247243,
            "unit": "iter/sec",
            "range": "stddev: 0.000013102847968880178",
            "extra": "mean: 61.38833199992178 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 24613.700280970166,
            "unit": "iter/sec",
            "range": "stddev: 0.00001050552541831487",
            "extra": "mean: 40.627779999951485 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 22028.987856988653,
            "unit": "iter/sec",
            "range": "stddev: 0.000011546267422954497",
            "extra": "mean: 45.394732000033855 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3233.6771592310965,
            "unit": "iter/sec",
            "range": "stddev: 0.00007247923135473513",
            "extra": "mean: 309.24546600000724 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "76c9abb94f379f68df65968259524382c0c4991f",
          "message": "Require `websockets >= 10` for `python_version >= '3.10'` (master) (#741)\n\n* Require `websockets >= 10` for `python_version >= '3.10'`.\r\n\r\n* Adapt `test_communication_engine.py` to the two possible ways of initializing the `ConnectionClosedOK` exception.",
          "timestamp": "2022-01-21T10:06:29+01:00",
          "tree_id": "0ac58ea62afb8018c40dad820cc06f8342dcab2b",
          "url": "https://github.com/simphony/osp-core/commit/76c9abb94f379f68df65968259524382c0c4991f"
        },
        "date": 1642756045867,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 641.7940528169509,
            "unit": "iter/sec",
            "range": "stddev: 0.004039196389631196",
            "extra": "mean: 1.5581322319999975 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1741.0822515739526,
            "unit": "iter/sec",
            "range": "stddev: 0.0000956047928544434",
            "extra": "mean: 574.3554040000074 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2142.347582424092,
            "unit": "iter/sec",
            "range": "stddev: 0.00008505337933884914",
            "extra": "mean: 466.7776640000163 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 303.9815465886419,
            "unit": "iter/sec",
            "range": "stddev: 0.00020953403783670877",
            "extra": "mean: 3.2896733740000137 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 489.8113436261258,
            "unit": "iter/sec",
            "range": "stddev: 0.0002242868880541574",
            "extra": "mean: 2.041602370000035 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 955.2998245947251,
            "unit": "iter/sec",
            "range": "stddev: 0.00016322637709600206",
            "extra": "mean: 1.0467917759999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 41.34991569242605,
            "unit": "iter/sec",
            "range": "stddev: 0.001690286089903198",
            "extra": "mean: 24.183846163999974 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 14041.945707064475,
            "unit": "iter/sec",
            "range": "stddev: 0.0003581613825870895",
            "extra": "mean: 71.21520199988396 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 17499.69839271714,
            "unit": "iter/sec",
            "range": "stddev: 0.00023580206790077635",
            "extra": "mean: 57.14384199993816 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 907.9933284064819,
            "unit": "iter/sec",
            "range": "stddev: 0.0002643473539770749",
            "extra": "mean: 1.101329677999935 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 41.470169192943956,
            "unit": "iter/sec",
            "range": "stddev: 0.0022691765088415756",
            "extra": "mean: 24.11371883600001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 13058.460061780464,
            "unit": "iter/sec",
            "range": "stddev: 0.000052481624580506605",
            "extra": "mean: 76.57870799994271 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 16242.674919042875,
            "unit": "iter/sec",
            "range": "stddev: 0.000012636229798818425",
            "extra": "mean: 61.566214000109206 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 20891.1591915287,
            "unit": "iter/sec",
            "range": "stddev: 0.000017535044692149393",
            "extra": "mean: 47.86713799995823 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 19693.195764472435,
            "unit": "iter/sec",
            "range": "stddev: 0.00001721829252828389",
            "extra": "mean: 50.77896000018711 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3074.5430967584457,
            "unit": "iter/sec",
            "range": "stddev: 0.00008067130620565246",
            "extra": "mean: 325.25158000039767 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "5090c744fda1b786a5d35f7848cb81486d386495",
          "message": "Set the default `ping_timeout` for the websockets socket spawned by the `CommunicationEngineClient` to `None`. (#744)",
          "timestamp": "2022-01-24T11:24:45+01:00",
          "tree_id": "f083a418e902f4ab46f4b31a13825a8a3541b337",
          "url": "https://github.com/simphony/osp-core/commit/5090c744fda1b786a5d35f7848cb81486d386495"
        },
        "date": 1643019955265,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 367.32647059492297,
            "unit": "iter/sec",
            "range": "stddev: 0.0058340524003608766",
            "extra": "mean: 2.7223739099999986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1009.9083563105758,
            "unit": "iter/sec",
            "range": "stddev: 0.00018554141211137758",
            "extra": "mean: 990.1888559999907 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1328.4874468710184,
            "unit": "iter/sec",
            "range": "stddev: 0.0002216167377725912",
            "extra": "mean: 752.7357540000068 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 213.60229414229633,
            "unit": "iter/sec",
            "range": "stddev: 0.0012489560223428028",
            "extra": "mean: 4.681597657999992 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 396.130666007245,
            "unit": "iter/sec",
            "range": "stddev: 0.0005472715436391004",
            "extra": "mean: 2.5244195560000158 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 754.6351502049971,
            "unit": "iter/sec",
            "range": "stddev: 0.00029841137623426895",
            "extra": "mean: 1.3251436799999965 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 31.569959977714884,
            "unit": "iter/sec",
            "range": "stddev: 0.00647596407740303",
            "extra": "mean: 31.675681587999993 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 11670.837746281255,
            "unit": "iter/sec",
            "range": "stddev: 0.00040058818165267056",
            "extra": "mean: 85.68365199992911 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 15598.606183393582,
            "unit": "iter/sec",
            "range": "stddev: 0.0002668155082923678",
            "extra": "mean: 64.10829200012813 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 569.1161108788046,
            "unit": "iter/sec",
            "range": "stddev: 0.0003498190989089887",
            "extra": "mean: 1.7571106860001606 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 35.56105567814403,
            "unit": "iter/sec",
            "range": "stddev: 0.004278897592292059",
            "extra": "mean: 28.120649990000274 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 9956.611675017628,
            "unit": "iter/sec",
            "range": "stddev: 0.0000688032819928267",
            "extra": "mean: 100.43577400021775 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 11386.289386388573,
            "unit": "iter/sec",
            "range": "stddev: 0.0000315388781372137",
            "extra": "mean: 87.82492399986097 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 19761.417247707963,
            "unit": "iter/sec",
            "range": "stddev: 0.000015376169474943576",
            "extra": "mean: 50.60365800008526 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 17329.948493982745,
            "unit": "iter/sec",
            "range": "stddev: 0.000018970219338213387",
            "extra": "mean: 57.70357600007969 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3241.0825519105774,
            "unit": "iter/sec",
            "range": "stddev: 0.00010202545169570417",
            "extra": "mean: 308.5388859998375 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "cbfa060e590f0912e70df016882f9490696a12f9",
          "message": "Bump package version to 3.6.1 (#746)",
          "timestamp": "2022-02-01T15:46:10+01:00",
          "tree_id": "818b13ac6d12e9181eb975c04a6a0c1680bd870c",
          "url": "https://github.com/simphony/osp-core/commit/cbfa060e590f0912e70df016882f9490696a12f9"
        },
        "date": 1643726836105,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 584.4114678819248,
            "unit": "iter/sec",
            "range": "stddev: 0.00438141346691049",
            "extra": "mean: 1.7111231639999942 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1515.5092350328873,
            "unit": "iter/sec",
            "range": "stddev: 0.00018214010829673154",
            "extra": "mean: 659.8442139999889 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2057.5589694034916,
            "unit": "iter/sec",
            "range": "stddev: 0.00010353642873900027",
            "extra": "mean: 486.01280199998877 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 265.1233321396069,
            "unit": "iter/sec",
            "range": "stddev: 0.0009009057982193133",
            "extra": "mean: 3.7718294799999974 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 415.14868794365617,
            "unit": "iter/sec",
            "range": "stddev: 0.0006236165956279039",
            "extra": "mean: 2.40877552800003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 832.7852385045521,
            "unit": "iter/sec",
            "range": "stddev: 0.0003341152622035722",
            "extra": "mean: 1.2007897760000148 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 40.88853770759691,
            "unit": "iter/sec",
            "range": "stddev: 0.0021296156536114164",
            "extra": "mean: 24.45673179000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17476.664022176774,
            "unit": "iter/sec",
            "range": "stddev: 0.0002906469286702761",
            "extra": "mean: 57.219158000123116 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 17435.115913527836,
            "unit": "iter/sec",
            "range": "stddev: 0.00022772654923959663",
            "extra": "mean: 57.355512000015096 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 996.3955649499276,
            "unit": "iter/sec",
            "range": "stddev: 0.00007241059849790047",
            "extra": "mean: 1.0036174740001513 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 38.431813738826136,
            "unit": "iter/sec",
            "range": "stddev: 0.0039847842147433",
            "extra": "mean: 26.020109454000078 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 12001.383615558825,
            "unit": "iter/sec",
            "range": "stddev: 0.00005838134966410565",
            "extra": "mean: 83.32372599969062 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 14955.372271843942,
            "unit": "iter/sec",
            "range": "stddev: 0.000017384362374512794",
            "extra": "mean: 66.8656039998865 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 19438.236519630267,
            "unit": "iter/sec",
            "range": "stddev: 0.000015813162284498783",
            "extra": "mean: 51.444996000029164 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 18729.749862685632,
            "unit": "iter/sec",
            "range": "stddev: 0.000021569199408754743",
            "extra": "mean: 53.39099600001873 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3720.11641642832,
            "unit": "iter/sec",
            "range": "stddev: 0.00007250842886005838",
            "extra": "mean: 268.8087920001436 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "07adcd8e27351b7847c638d8638f22e9c10d6ec9",
          "message": "Bump package version to 3.6.1 (dev) (#747)",
          "timestamp": "2022-02-01T15:58:16+01:00",
          "tree_id": "5b4c198c73c4a847b1e8d0fdf65f21a0e776af0f",
          "url": "https://github.com/simphony/osp-core/commit/07adcd8e27351b7847c638d8638f22e9c10d6ec9"
        },
        "date": 1643727555410,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 596.1344202424885,
            "unit": "iter/sec",
            "range": "stddev: 0.003959064294596662",
            "extra": "mean: 1.677474016000002 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1585.4808864840777,
            "unit": "iter/sec",
            "range": "stddev: 0.00017606498828442416",
            "extra": "mean: 630.7234660000063 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2161.3005953120914,
            "unit": "iter/sec",
            "range": "stddev: 0.00008471494755569912",
            "extra": "mean: 462.6843680000006 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 307.2276871664786,
            "unit": "iter/sec",
            "range": "stddev: 0.0002170446643986078",
            "extra": "mean: 3.254914975999954 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 446.5008878286183,
            "unit": "iter/sec",
            "range": "stddev: 0.0005462411562039931",
            "extra": "mean: 2.2396372039999903 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 1004.5458492315573,
            "unit": "iter/sec",
            "range": "stddev: 0.00010631043680626267",
            "extra": "mean: 995.4747219999618 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 42.30951102368223,
            "unit": "iter/sec",
            "range": "stddev: 0.0013840073836430562",
            "extra": "mean: 23.635347604000017 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17711.929076292636,
            "unit": "iter/sec",
            "range": "stddev: 0.00028809429975547134",
            "extra": "mean: 56.459124000134864 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 18266.178034212346,
            "unit": "iter/sec",
            "range": "stddev: 0.00022560949717800237",
            "extra": "mean: 54.74599000004332 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 687.8406298573193,
            "unit": "iter/sec",
            "range": "stddev: 0.0002414416924787522",
            "extra": "mean: 1.4538251399999922 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 40.969892745476486,
            "unit": "iter/sec",
            "range": "stddev: 0.001367499723727502",
            "extra": "mean: 24.408167388000074 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 11800.080580392374,
            "unit": "iter/sec",
            "range": "stddev: 0.00005881731654351675",
            "extra": "mean: 84.74518399998487 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 16324.575927515338,
            "unit": "iter/sec",
            "range": "stddev: 0.000011857992566054331",
            "extra": "mean: 61.25733399998979 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 21486.22726384279,
            "unit": "iter/sec",
            "range": "stddev: 0.000018600553716285705",
            "extra": "mean: 46.541442000048505 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 20747.06702864559,
            "unit": "iter/sec",
            "range": "stddev: 0.000012709081672528427",
            "extra": "mean: 48.19958399995983 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3015.862550352648,
            "unit": "iter/sec",
            "range": "stddev: 0.00007646226892469533",
            "extra": "mean: 331.5800979998471 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "e777da3d629629782aa1787066a30c9c88b24e11",
          "message": "749 Error when installing ontologies with label languages both defined and undefined, and with duplicate label definitions (#750)\n\n*Fix bug when installing ontologies with labels which have a language assigned and labels which have no language assigned.\r\n\r\n* Fix problems when installing ontologies in which the same entity has both an RDFS label and an SKOS label, and they are equal.",
          "timestamp": "2022-02-04T08:30:43+01:00",
          "tree_id": "0eb6ce79cba36b79b36c0d265f0053478bcd55f1",
          "url": "https://github.com/simphony/osp-core/commit/e777da3d629629782aa1787066a30c9c88b24e11"
        },
        "date": 1643959913620,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 460.7856381860456,
            "unit": "iter/sec",
            "range": "stddev: 0.006233745563664804",
            "extra": "mean: 2.170206527999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1073.2415539227472,
            "unit": "iter/sec",
            "range": "stddev: 0.00026508988031149306",
            "extra": "mean: 931.7566920000013 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1254.0855442098,
            "unit": "iter/sec",
            "range": "stddev: 0.0001604363088663997",
            "extra": "mean: 797.3937700000367 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 256.7284621231655,
            "unit": "iter/sec",
            "range": "stddev: 0.000617056621639667",
            "extra": "mean: 3.895166089999986 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 301.3869196141992,
            "unit": "iter/sec",
            "range": "stddev: 0.0006353265962992553",
            "extra": "mean: 3.3179940299999906 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 767.1028448217746,
            "unit": "iter/sec",
            "range": "stddev: 0.000318769623861812",
            "extra": "mean: 1.303606167999984 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 32.25156901267645,
            "unit": "iter/sec",
            "range": "stddev: 0.005234329727012013",
            "extra": "mean: 31.006243435999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 16360.450299809308,
            "unit": "iter/sec",
            "range": "stddev: 0.0003173071399906084",
            "extra": "mean: 61.1230119999604 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 15243.51995681652,
            "unit": "iter/sec",
            "range": "stddev: 0.00025810705170416416",
            "extra": "mean: 65.60164599993357 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 871.0042997841782,
            "unit": "iter/sec",
            "range": "stddev: 0.000174055783806282",
            "extra": "mean: 1.1480999579999605 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 30.62595058774007,
            "unit": "iter/sec",
            "range": "stddev: 0.006419093240849877",
            "extra": "mean: 32.652047718000034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 9866.03172043907,
            "unit": "iter/sec",
            "range": "stddev: 0.00008244098514841452",
            "extra": "mean: 101.35787399997298 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 13220.972343872229,
            "unit": "iter/sec",
            "range": "stddev: 0.000021137839197063976",
            "extra": "mean: 75.63740199967128 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 21367.2793875058,
            "unit": "iter/sec",
            "range": "stddev: 0.000016134797565860186",
            "extra": "mean: 46.80053000031137 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 17822.452725905998,
            "unit": "iter/sec",
            "range": "stddev: 0.000018773247985287112",
            "extra": "mean: 56.10900000012009 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2475.4308414358616,
            "unit": "iter/sec",
            "range": "stddev: 0.00011581437148534312",
            "extra": "mean: 403.9700819999297 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "90d7e93e7f2c4e3ce16750ef8967ba1801618ccb",
          "message": "Improve the warning provided when CUDS objects are unreachable from the wrapper object and add an option to disable it (#748)\n\n* Improve warning about CUDS objects unreachable from the wrapper object and offer the option to disable it (needed for improving performance with large datasets).\r\n\r\n * Make the unreachable CUDS warning load as little cuds as possible (use the registry to make it faster).\r\n\r\n* Simplify subtree algorithm code.\r\n\r\n* Test the warnings.\r\n\r\n* Raise large dataset warning during the computation of the unreachable CUDS warning if possible.",
          "timestamp": "2022-02-10T09:33:21+01:00",
          "tree_id": "328978606d4616c204e50787ae37e3d6f463c011",
          "url": "https://github.com/simphony/osp-core/commit/90d7e93e7f2c4e3ce16750ef8967ba1801618ccb"
        },
        "date": 1644482066983,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 481.1881485445444,
            "unit": "iter/sec",
            "range": "stddev: 0.004623739020996924",
            "extra": "mean: 2.0781891720000005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1398.1627783163506,
            "unit": "iter/sec",
            "range": "stddev: 0.00011389063557912395",
            "extra": "mean: 715.224303999987 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1725.90715846269,
            "unit": "iter/sec",
            "range": "stddev: 0.00011960643831140573",
            "extra": "mean: 579.4054419999775 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 290.6001927528997,
            "unit": "iter/sec",
            "range": "stddev: 0.00044766828381468906",
            "extra": "mean: 3.4411539459999947 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 469.4455522420517,
            "unit": "iter/sec",
            "range": "stddev: 0.0002758923677283026",
            "extra": "mean: 2.1301724880000314 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 980.9003267019699,
            "unit": "iter/sec",
            "range": "stddev: 0.0000872995097813714",
            "extra": "mean: 1.019471574000029 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 37.970332991025685,
            "unit": "iter/sec",
            "range": "stddev: 0.0037555043700430966",
            "extra": "mean: 26.33635054599997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 12444.870468316232,
            "unit": "iter/sec",
            "range": "stddev: 0.0005789153114578808",
            "extra": "mean: 80.3543919999754 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 17621.886269948798,
            "unit": "iter/sec",
            "range": "stddev: 0.00024561391897574565",
            "extra": "mean: 56.74761400005934 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 881.9480191266683,
            "unit": "iter/sec",
            "range": "stddev: 0.00019892060252147477",
            "extra": "mean: 1.1338536720001144 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 39.84869229657473,
            "unit": "iter/sec",
            "range": "stddev: 0.002156679797638886",
            "extra": "mean: 25.09492639199999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 12618.169472534772,
            "unit": "iter/sec",
            "range": "stddev: 0.00005306300441076672",
            "extra": "mean: 79.25079800018864 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 14946.798812710565,
            "unit": "iter/sec",
            "range": "stddev: 0.000016977108895239977",
            "extra": "mean: 66.90395799999749 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 21186.343723463826,
            "unit": "iter/sec",
            "range": "stddev: 0.000015568666629655053",
            "extra": "mean: 47.20021600010682 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 20593.521772351723,
            "unit": "iter/sec",
            "range": "stddev: 0.00001580296220945267",
            "extra": "mean: 48.55895999986615 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2677.6354180787903,
            "unit": "iter/sec",
            "range": "stddev: 0.00010212122150875138",
            "extra": "mean: 373.46383799983585 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "d0177ed36b2a3a10640e5787bc11e690acc775b3",
          "message": "733 Publish OSP-core in PyPI (3.x branch) (#752)\n\n* Update `setup.py`.\r\n\r\n* Change README for PyPI release.",
          "timestamp": "2022-02-10T09:49:11+01:00",
          "tree_id": "252563c386706076c06f6c617324e25ca8a38f45",
          "url": "https://github.com/simphony/osp-core/commit/d0177ed36b2a3a10640e5787bc11e690acc775b3"
        },
        "date": 1644483030625,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 377.6673700288385,
            "unit": "iter/sec",
            "range": "stddev: 0.006285026203711919",
            "extra": "mean: 2.647832667999993 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1092.8690406569685,
            "unit": "iter/sec",
            "range": "stddev: 0.00016307718563007142",
            "extra": "mean: 915.0227180000074 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1230.2696519540418,
            "unit": "iter/sec",
            "range": "stddev: 0.0002040310184868247",
            "extra": "mean: 812.8299339999945 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 185.509347723463,
            "unit": "iter/sec",
            "range": "stddev: 0.0012252054918156273",
            "extra": "mean: 5.390563937999989 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 329.1112619321291,
            "unit": "iter/sec",
            "range": "stddev: 0.0007535281705345123",
            "extra": "mean: 3.0384861159999588 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 540.5390661837001,
            "unit": "iter/sec",
            "range": "stddev: 0.00019302899060641312",
            "extra": "mean: 1.8500050460000494 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 25.51684074893178,
            "unit": "iter/sec",
            "range": "stddev: 0.007046914052774348",
            "extra": "mean: 39.18980448399998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 9442.80518396012,
            "unit": "iter/sec",
            "range": "stddev: 0.0005813298035810495",
            "extra": "mean: 105.90073399995958 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 10476.494214709868,
            "unit": "iter/sec",
            "range": "stddev: 0.00040136426644871577",
            "extra": "mean: 95.45177799992643 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 613.3283748268577,
            "unit": "iter/sec",
            "range": "stddev: 0.0003261288835308999",
            "extra": "mean: 1.6304479640001972 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 28.08058359656756,
            "unit": "iter/sec",
            "range": "stddev: 0.006604051912225608",
            "extra": "mean: 35.611795479999756 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6266.163254818878,
            "unit": "iter/sec",
            "range": "stddev: 0.00011319409066193113",
            "extra": "mean: 159.5872879997131 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8059.443879026876,
            "unit": "iter/sec",
            "range": "stddev: 0.000023827347024000157",
            "extra": "mean: 124.07804000004319 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 12479.744438772013,
            "unit": "iter/sec",
            "range": "stddev: 0.00002143682553390282",
            "extra": "mean: 80.12984600014761 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 11098.364762475438,
            "unit": "iter/sec",
            "range": "stddev: 0.000021446357086982783",
            "extra": "mean: 90.10336400017138 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2468.6704611344276,
            "unit": "iter/sec",
            "range": "stddev: 0.00003498420776054137",
            "extra": "mean: 405.07634200008624 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "cb691b0ea91e7e56c587cde6755272d4ca92f416",
          "message": "Bump package version to 3.7.0 (#753)\n\nBump minor package version due to PR [#748](https://github.com/simphony/osp-core/pull/748). Old code works with the new version, but new code will not work with an old version in general (code turning the warning off).",
          "timestamp": "2022-02-10T09:57:35+01:00",
          "tree_id": "cd3523ad93a9e39a9a0ccf6ee33680ee300f2bd1",
          "url": "https://github.com/simphony/osp-core/commit/cb691b0ea91e7e56c587cde6755272d4ca92f416"
        },
        "date": 1644483531474,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 415.4424902433153,
            "unit": "iter/sec",
            "range": "stddev: 0.006516777273407812",
            "extra": "mean: 2.4070720339999947 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1295.0796404433156,
            "unit": "iter/sec",
            "range": "stddev: 0.00016394791502413866",
            "extra": "mean: 772.1532859999963 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1308.6903759781278,
            "unit": "iter/sec",
            "range": "stddev: 0.00021603984902889047",
            "extra": "mean: 764.1226820000036 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 158.45120638735298,
            "unit": "iter/sec",
            "range": "stddev: 0.000861094287499407",
            "extra": "mean: 6.311091110000008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 326.2969716800301,
            "unit": "iter/sec",
            "range": "stddev: 0.0007565702034502917",
            "extra": "mean: 3.064692861999987 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 789.2462184656366,
            "unit": "iter/sec",
            "range": "stddev: 0.0002402800264676609",
            "extra": "mean: 1.267031728000024 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 30.433913163401833,
            "unit": "iter/sec",
            "range": "stddev: 0.005683255614090846",
            "extra": "mean: 32.85808153000008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 13018.924908118302,
            "unit": "iter/sec",
            "range": "stddev: 0.00038492344173021465",
            "extra": "mean: 76.81125799999222 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 10086.797294190614,
            "unit": "iter/sec",
            "range": "stddev: 0.0003460992837575518",
            "extra": "mean: 99.13949599997807 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 565.1928018297967,
            "unit": "iter/sec",
            "range": "stddev: 0.0005078432231191199",
            "extra": "mean: 1.7693077419997678 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 29.52653596645916,
            "unit": "iter/sec",
            "range": "stddev: 0.0065094713786235285",
            "extra": "mean: 33.86784014000003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 11551.414050189125,
            "unit": "iter/sec",
            "range": "stddev: 0.00006124888078737219",
            "extra": "mean: 86.56948799992392 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 13569.760169385705,
            "unit": "iter/sec",
            "range": "stddev: 0.000025594400591067343",
            "extra": "mean: 73.69327000016312 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 22364.649254591193,
            "unit": "iter/sec",
            "range": "stddev: 0.000015095020894999856",
            "extra": "mean: 44.71342199988726 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 20564.030220862463,
            "unit": "iter/sec",
            "range": "stddev: 0.000015519906991149698",
            "extra": "mean: 48.62860000008595 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3035.7899538635324,
            "unit": "iter/sec",
            "range": "stddev: 0.00010134295851792342",
            "extra": "mean: 329.4035539999527 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "328f4ed94bae3285efab2e62e1039646bf14f2a8",
          "message": "Fix package homepage URL (#754)",
          "timestamp": "2022-02-10T12:10:01+01:00",
          "tree_id": "e71dc72a46b7a4e6e7c662a4b7c492280613119b",
          "url": "https://github.com/simphony/osp-core/commit/328f4ed94bae3285efab2e62e1039646bf14f2a8"
        },
        "date": 1644491463675,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 616.0495599451414,
            "unit": "iter/sec",
            "range": "stddev: 0.004084232994724532",
            "extra": "mean: 1.6232460260000008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1195.4625816039763,
            "unit": "iter/sec",
            "range": "stddev: 0.0002371405257796025",
            "extra": "mean: 836.4962780000021 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1818.8242401312373,
            "unit": "iter/sec",
            "range": "stddev: 0.00014708108857850748",
            "extra": "mean: 549.8057360000024 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 264.3014499067431,
            "unit": "iter/sec",
            "range": "stddev: 0.0009376731343096929",
            "extra": "mean: 3.783558510000013 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 437.4784559359571,
            "unit": "iter/sec",
            "range": "stddev: 0.000308970120368865",
            "extra": "mean: 2.28582684800001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 922.1017224813598,
            "unit": "iter/sec",
            "range": "stddev: 0.00012218119283807365",
            "extra": "mean: 1.0844790500000556 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 39.34550046418299,
            "unit": "iter/sec",
            "range": "stddev: 0.0025920632157370757",
            "extra": "mean: 25.4158668260001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17310.87950692778,
            "unit": "iter/sec",
            "range": "stddev: 0.00028556259113212795",
            "extra": "mean: 57.76714000000993 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 18133.734113030358,
            "unit": "iter/sec",
            "range": "stddev: 0.00022372448612230012",
            "extra": "mean: 55.14584000001577 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 918.4500739862058,
            "unit": "iter/sec",
            "range": "stddev: 0.00018480662715120313",
            "extra": "mean: 1.088790809999999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 40.95239041651725,
            "unit": "iter/sec",
            "range": "stddev: 0.0015004200946911047",
            "extra": "mean: 24.41859900800008 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 11348.739080188087,
            "unit": "iter/sec",
            "range": "stddev: 0.00006814392414055483",
            "extra": "mean: 88.11551599998779 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 15795.208675119431,
            "unit": "iter/sec",
            "range": "stddev: 0.000014969660828988332",
            "extra": "mean: 63.31033799985163 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 23895.424446753306,
            "unit": "iter/sec",
            "range": "stddev: 0.000011973224389802599",
            "extra": "mean: 41.84901600004309 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12882.365350683895,
            "unit": "iter/sec",
            "range": "stddev: 0.00001861603830178321",
            "extra": "mean: 77.62549599999602 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3063.5258729517764,
            "unit": "iter/sec",
            "range": "stddev: 0.00006543983129577578",
            "extra": "mean: 326.4212680000895 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "635eb428cc855a078cd7ad4b6c19caafb2325ecc",
          "message": "Merge branch 'master' into dev",
          "timestamp": "2022-02-10T12:14:17+01:00",
          "tree_id": "e71dc72a46b7a4e6e7c662a4b7c492280613119b",
          "url": "https://github.com/simphony/osp-core/commit/635eb428cc855a078cd7ad4b6c19caafb2325ecc"
        },
        "date": 1644491715106,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 607.6365250140163,
            "unit": "iter/sec",
            "range": "stddev: 0.00425757155642059",
            "extra": "mean: 1.6457206880000061 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1756.456883044433,
            "unit": "iter/sec",
            "range": "stddev: 0.00008497178955291957",
            "extra": "mean: 569.3279520000054 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1928.343466418332,
            "unit": "iter/sec",
            "range": "stddev: 0.00011019293230869396",
            "extra": "mean: 518.5798159999893 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 264.49111034375,
            "unit": "iter/sec",
            "range": "stddev: 0.0006749154029907661",
            "extra": "mean: 3.7808454080000438 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 465.09750427330164,
            "unit": "iter/sec",
            "range": "stddev: 0.00025552976934833217",
            "extra": "mean: 2.150086790000012 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 903.8104278885464,
            "unit": "iter/sec",
            "range": "stddev: 0.0002182663829067333",
            "extra": "mean: 1.1064267119999585 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 39.5442483836507,
            "unit": "iter/sec",
            "range": "stddev: 0.0033759801103295825",
            "extra": "mean: 25.288127625999923 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17111.267591763313,
            "unit": "iter/sec",
            "range": "stddev: 0.0003168282234679533",
            "extra": "mean: 58.44102399996132 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 14589.039167347659,
            "unit": "iter/sec",
            "range": "stddev: 0.0002968885135548293",
            "extra": "mean: 68.54460999996093 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 965.1504871230412,
            "unit": "iter/sec",
            "range": "stddev: 0.0001935574041226368",
            "extra": "mean: 1.0361078539998871 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 34.970176823325275,
            "unit": "iter/sec",
            "range": "stddev: 0.006735924104723325",
            "extra": "mean: 28.595794783999928 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 11552.723731376334,
            "unit": "iter/sec",
            "range": "stddev: 0.00005475464459677695",
            "extra": "mean: 86.55967400000009 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 15647.727346027857,
            "unit": "iter/sec",
            "range": "stddev: 0.000015393623801881135",
            "extra": "mean: 63.90704399983349 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 22654.018897727678,
            "unit": "iter/sec",
            "range": "stddev: 0.000017784265023640967",
            "extra": "mean: 44.14227799996695 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 18885.624277889903,
            "unit": "iter/sec",
            "range": "stddev: 0.00002070254024985459",
            "extra": "mean: 52.95032800005117 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2923.852814651761,
            "unit": "iter/sec",
            "range": "stddev: 0.00011632229781648808",
            "extra": "mean: 342.0144800001168 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "638fc6a19e22de7cd0b7e477ed91b47f6a66e074",
          "message": "Merge pull request #755 from simphony/dev\n\nMerge release 3.7.0.",
          "timestamp": "2022-02-10T13:11:12+01:00",
          "tree_id": "e71dc72a46b7a4e6e7c662a4b7c492280613119b",
          "url": "https://github.com/simphony/osp-core/commit/638fc6a19e22de7cd0b7e477ed91b47f6a66e074"
        },
        "date": 1644495147667,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 385.5192011685611,
            "unit": "iter/sec",
            "range": "stddev: 0.006598974796613531",
            "extra": "mean: 2.5939045240000085 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1102.8966316109766,
            "unit": "iter/sec",
            "range": "stddev: 0.00018802817329449106",
            "extra": "mean: 906.7032859999964 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1344.0068190389877,
            "unit": "iter/sec",
            "range": "stddev: 0.00022568463722536002",
            "extra": "mean: 744.0438440000144 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 202.0031183512272,
            "unit": "iter/sec",
            "range": "stddev: 0.000895573124218484",
            "extra": "mean: 4.950418627999982 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 288.3646163966868,
            "unit": "iter/sec",
            "range": "stddev: 0.0009759221792346276",
            "extra": "mean: 3.467831845999985 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 620.5626527885838,
            "unit": "iter/sec",
            "range": "stddev: 0.00036639174132679887",
            "extra": "mean: 1.6114408359999786 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 27.236953281223922,
            "unit": "iter/sec",
            "range": "stddev: 0.008037466655643357",
            "extra": "mean: 36.714825981999994 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 11438.157781273643,
            "unit": "iter/sec",
            "range": "stddev: 0.00041530348759772685",
            "extra": "mean: 87.42666600011262 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 13899.258121560157,
            "unit": "iter/sec",
            "range": "stddev: 0.0002473868507783556",
            "extra": "mean: 71.94628599988562 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 804.4920752237126,
            "unit": "iter/sec",
            "range": "stddev: 0.00021431720750206965",
            "extra": "mean: 1.2430203239999855 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 29.906400278048352,
            "unit": "iter/sec",
            "range": "stddev: 0.007850371925362429",
            "extra": "mean: 33.437658517999964 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 6804.397191986568,
            "unit": "iter/sec",
            "range": "stddev: 0.00010118231278397455",
            "extra": "mean: 146.96379000004356 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8653.037094885041,
            "unit": "iter/sec",
            "range": "stddev: 0.000021429817896318477",
            "extra": "mean: 115.56635999990306 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 13328.58196046166,
            "unit": "iter/sec",
            "range": "stddev: 0.000019742996625737058",
            "extra": "mean: 75.02673599985599 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 12089.186181820303,
            "unit": "iter/sec",
            "range": "stddev: 0.000019560577453230282",
            "extra": "mean: 82.71855400025174 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2014.101424984275,
            "unit": "iter/sec",
            "range": "stddev: 0.00012273651813812016",
            "extra": "mean: 496.49932599983515 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "272329f1e064b1c9c34b38b14cfa97638ca2495c",
          "message": "Stop assigning an UID to imported CUDS with custom IRIs (#759)",
          "timestamp": "2022-02-25T16:54:26+01:00",
          "tree_id": "7187c0aadd7ae8ef62d909feeded4fbd21ad7512",
          "url": "https://github.com/simphony/osp-core/commit/272329f1e064b1c9c34b38b14cfa97638ca2495c"
        },
        "date": 1645804538788,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 405.5782870964479,
            "unit": "iter/sec",
            "range": "stddev: 0.005876106439566661",
            "extra": "mean: 2.4656152259999966 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1344.2227275113698,
            "unit": "iter/sec",
            "range": "stddev: 0.00013377842954597743",
            "extra": "mean: 743.9243359999965 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1877.0709395187282,
            "unit": "iter/sec",
            "range": "stddev: 0.00012213621803696556",
            "extra": "mean: 532.7449160000288 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 248.91301453833398,
            "unit": "iter/sec",
            "range": "stddev: 0.0007574381840021809",
            "extra": "mean: 4.017467716000018 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 338.7559435805881,
            "unit": "iter/sec",
            "range": "stddev: 0.000679082122248924",
            "extra": "mean: 2.951977725999974 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 600.2923531812764,
            "unit": "iter/sec",
            "range": "stddev: 0.00027671070679456943",
            "extra": "mean: 1.665854969999959 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 30.24073139062015,
            "unit": "iter/sec",
            "range": "stddev: 0.006936615396343954",
            "extra": "mean: 33.06798328000006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 9433.070927948425,
            "unit": "iter/sec",
            "range": "stddev: 0.0005319600138544097",
            "extra": "mean: 106.01001599989957 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 13134.88104264165,
            "unit": "iter/sec",
            "range": "stddev: 0.00027756977266440227",
            "extra": "mean: 76.13315999996928 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 666.8817938416427,
            "unit": "iter/sec",
            "range": "stddev: 0.00043185836975912574",
            "extra": "mean: 1.4995161199999103 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 32.05513295769345,
            "unit": "iter/sec",
            "range": "stddev: 0.005558406903870597",
            "extra": "mean: 31.196251823999788 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 9728.041320363229,
            "unit": "iter/sec",
            "range": "stddev: 0.00007900089083807301",
            "extra": "mean: 102.79561599998033 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 11802.752680474547,
            "unit": "iter/sec",
            "range": "stddev: 0.00002937161015247068",
            "extra": "mean: 84.72599799996772 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 18346.88409730534,
            "unit": "iter/sec",
            "range": "stddev: 0.000022310388005633165",
            "extra": "mean: 54.5051679999915 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 13040.837774755386,
            "unit": "iter/sec",
            "range": "stddev: 0.000027063918228830995",
            "extra": "mean: 76.68218999977228 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2426.7554486409135,
            "unit": "iter/sec",
            "range": "stddev: 0.0001236838542607594",
            "extra": "mean: 412.07283600003564 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "ebef2ad7707ba58152eedec407097788e27d73c8",
          "message": "Improve performance of `_load_first_level` for remote triplestores (#756)\n\n\"Vectorize\" several methods of the class `TripleStoreWrapperSession` so that `_load_first_level` improves its performance.",
          "timestamp": "2022-03-09T16:37:29+01:00",
          "tree_id": "d0b4646f9cacf137fb184f94fd9dba953268d59b",
          "url": "https://github.com/simphony/osp-core/commit/ebef2ad7707ba58152eedec407097788e27d73c8"
        },
        "date": 1646840343023,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 380.23972132620037,
            "unit": "iter/sec",
            "range": "stddev: 0.006516308169570843",
            "extra": "mean: 2.6299198740000107 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1397.3234905717575,
            "unit": "iter/sec",
            "range": "stddev: 0.0001516124135882079",
            "extra": "mean: 715.6538960000019 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1422.366893497996,
            "unit": "iter/sec",
            "range": "stddev: 0.00018315371249022136",
            "extra": "mean: 703.0534839999838 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 226.88308300988515,
            "unit": "iter/sec",
            "range": "stddev: 0.0008890677297738109",
            "extra": "mean: 4.407556467999999 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 376.5909135867132,
            "unit": "iter/sec",
            "range": "stddev: 0.0009171245540057006",
            "extra": "mean: 2.655401296000047 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 777.2238722589583,
            "unit": "iter/sec",
            "range": "stddev: 0.00024072982686874136",
            "extra": "mean: 1.286630578000075 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 30.512917990061176,
            "unit": "iter/sec",
            "range": "stddev: 0.007285137835991074",
            "extra": "mean: 32.773004545999996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 16001.574042827426,
            "unit": "iter/sec",
            "range": "stddev: 0.00031399334531186156",
            "extra": "mean: 62.49385200003133 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 14158.636878906433,
            "unit": "iter/sec",
            "range": "stddev: 0.0002607456702992358",
            "extra": "mean: 70.62826800013511 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 798.3123051991461,
            "unit": "iter/sec",
            "range": "stddev: 0.00025336938008967434",
            "extra": "mean: 1.2526425979999658 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 32.671055985531915,
            "unit": "iter/sec",
            "range": "stddev: 0.006097349436266656",
            "extra": "mean: 30.608132178000034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 7266.64506438626,
            "unit": "iter/sec",
            "range": "stddev: 0.00007732523948297838",
            "extra": "mean: 137.61508799996136 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 8727.13938927162,
            "unit": "iter/sec",
            "range": "stddev: 0.00004032851594827545",
            "extra": "mean: 114.58508400006906 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 13189.843662086723,
            "unit": "iter/sec",
            "range": "stddev: 0.000019687571712999045",
            "extra": "mean: 75.81591000008814 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 15575.66068759492,
            "unit": "iter/sec",
            "range": "stddev: 0.000021278590264283647",
            "extra": "mean: 64.20273400000553 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2513.2671477163135,
            "unit": "iter/sec",
            "range": "stddev: 0.0002001916081876076",
            "extra": "mean: 397.8884620000116 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "aab6d91b6223316a07821256463a30c7913f797c",
          "message": "Enable use of pico as a module (#761)",
          "timestamp": "2022-03-14T14:23:15+01:00",
          "tree_id": "92b22acbb6bfe85c5741b534202baa73984ff255",
          "url": "https://github.com/simphony/osp-core/commit/aab6d91b6223316a07821256463a30c7913f797c"
        },
        "date": 1647264265265,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 574.4704931400163,
            "unit": "iter/sec",
            "range": "stddev: 0.004598360927342244",
            "extra": "mean: 1.7407334440000017 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1640.5045454410554,
            "unit": "iter/sec",
            "range": "stddev: 0.00010949218634272539",
            "extra": "mean: 609.5685640000141 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1921.039453854901,
            "unit": "iter/sec",
            "range": "stddev: 0.0001165166903530568",
            "extra": "mean: 520.55151600001 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 286.6903561239684,
            "unit": "iter/sec",
            "range": "stddev: 0.0006042820933407976",
            "extra": "mean: 3.488083845999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 463.1232310452435,
            "unit": "iter/sec",
            "range": "stddev: 0.0002979161906560526",
            "extra": "mean: 2.1592525120000037 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 944.7951721480629,
            "unit": "iter/sec",
            "range": "stddev: 0.000210478449092429",
            "extra": "mean: 1.0584304720000048 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 38.034036415922735,
            "unit": "iter/sec",
            "range": "stddev: 0.004819745952725082",
            "extra": "mean: 26.292239642000123 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17684.029471630478,
            "unit": "iter/sec",
            "range": "stddev: 0.0002892998093816638",
            "extra": "mean: 56.548198000022865 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 17931.091318134182,
            "unit": "iter/sec",
            "range": "stddev: 0.00022263456941629359",
            "extra": "mean: 55.76905400000243 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 969.9247291854358,
            "unit": "iter/sec",
            "range": "stddev: 0.00013838803766778808",
            "extra": "mean: 1.031007839999937 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 40.89468664239217,
            "unit": "iter/sec",
            "range": "stddev: 0.0022539521979150715",
            "extra": "mean: 24.45305447000007 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 9296.111109512634,
            "unit": "iter/sec",
            "range": "stddev: 0.00008526860696944703",
            "extra": "mean: 107.5718639998513 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 13657.961964912887,
            "unit": "iter/sec",
            "range": "stddev: 0.00002277536956475915",
            "extra": "mean: 73.21736600006545 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 24125.67236436041,
            "unit": "iter/sec",
            "range": "stddev: 0.000011114875084069637",
            "extra": "mean: 41.44962200005864 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 22123.809617378407,
            "unit": "iter/sec",
            "range": "stddev: 0.000011339839513703293",
            "extra": "mean: 45.20017199996573 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3658.044025274863,
            "unit": "iter/sec",
            "range": "stddev: 0.00009209451282826303",
            "extra": "mean: 273.3701380001463 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "db42213eb1040d53b966c5c2531920e37cd5562e",
          "message": "Interpret `rdfs:Class` as classes on SimPhoNy v3, include dcmitype, dcterms, prov and datamodel namespaces (#760)\n\n* Bundle yml files for datamodel, dcterms, prov, dcmitype. Update dcat2 specs.\r\n\r\n* Add RDFS.Class as valid type on `namespace.py` and `namespace_registry.py`.\r\n\r\n* Validate ontology files before installation and warn about unsupported RDFS properties.\r\n\r\n* Fix bug with prov on Python 3.6 (format not guessed by RDFLib 5.0.0 because it is not on the URL).\r\n\r\nCo-authored-by: Matthias Büschelberger <matthias.bueschelberger@iwm.fraunhofer.de>",
          "timestamp": "2022-03-30T15:56:12+02:00",
          "tree_id": "beb57c5d1784cf8a94b7e62970e76ec78c052848",
          "url": "https://github.com/simphony/osp-core/commit/db42213eb1040d53b966c5c2531920e37cd5562e"
        },
        "date": 1648648892677,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 557.4983219913757,
            "unit": "iter/sec",
            "range": "stddev: 0.004222359937480882",
            "extra": "mean: 1.7937273719999998 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1610.05780700028,
            "unit": "iter/sec",
            "range": "stddev: 0.0001344826737229222",
            "extra": "mean: 621.0957120000016 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1499.3805714002167,
            "unit": "iter/sec",
            "range": "stddev: 0.0002304131303917908",
            "extra": "mean: 666.9420819999932 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 258.61458073288776,
            "unit": "iter/sec",
            "range": "stddev: 0.0009226494436014212",
            "extra": "mean: 3.8667580040000082 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 414.31573217077107,
            "unit": "iter/sec",
            "range": "stddev: 0.0005933564231335766",
            "extra": "mean: 2.413618219999968 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 920.0126146977439,
            "unit": "iter/sec",
            "range": "stddev: 0.00018053045495626768",
            "extra": "mean: 1.0869416180000258 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 34.14813155577838,
            "unit": "iter/sec",
            "range": "stddev: 0.006294614138914564",
            "extra": "mean: 29.28417908800006 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 14032.108776483366,
            "unit": "iter/sec",
            "range": "stddev: 0.0003595833198247905",
            "extra": "mean: 71.26512599987223 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 16696.82335587386,
            "unit": "iter/sec",
            "range": "stddev: 0.00022660389099680918",
            "extra": "mean: 59.89163200005976 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 927.5513445722056,
            "unit": "iter/sec",
            "range": "stddev: 0.00016480075113146355",
            "extra": "mean: 1.0781074340000103 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 33.953731741134824,
            "unit": "iter/sec",
            "range": "stddev: 0.0055098856988800606",
            "extra": "mean: 29.451843691999947 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 8424.377547169177,
            "unit": "iter/sec",
            "range": "stddev: 0.00010287762110266353",
            "extra": "mean: 118.70313200006422 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 12787.0706961604,
            "unit": "iter/sec",
            "range": "stddev: 0.000020554013624760605",
            "extra": "mean: 78.2039939999919 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 23587.509187225736,
            "unit": "iter/sec",
            "range": "stddev: 0.000012584396804841487",
            "extra": "mean: 42.39532000019608 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 19323.606525413674,
            "unit": "iter/sec",
            "range": "stddev: 0.00001756480761811777",
            "extra": "mean: 51.75017400011939 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3069.7693808136305,
            "unit": "iter/sec",
            "range": "stddev: 0.00011191992693136494",
            "extra": "mean: 325.75736999987726 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "5e0dc92ad97b2b244c1437fce59995a2977b8080",
          "message": "Cache access to namespace elements to improve performance (#764)\n\nCache requests of objects by label for namespace objects.",
          "timestamp": "2022-04-05T14:06:35+02:00",
          "tree_id": "0bf39a1f00f6e73891112b117a48fc6b27e1f361",
          "url": "https://github.com/simphony/osp-core/commit/5e0dc92ad97b2b244c1437fce59995a2977b8080"
        },
        "date": 1649162256097,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 463.4060555282303,
            "unit": "iter/sec",
            "range": "stddev: 0.006158474628842798",
            "extra": "mean: 2.157934684000004 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1561.8951463427404,
            "unit": "iter/sec",
            "range": "stddev: 0.00015860084128362505",
            "extra": "mean: 640.2478439999974 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 1611.9324265031441,
            "unit": "iter/sec",
            "range": "stddev: 0.0001493595836382085",
            "extra": "mean: 620.3733999999964 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 182.19148627718425,
            "unit": "iter/sec",
            "range": "stddev: 0.0009054350755848797",
            "extra": "mean: 5.488730678000016 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 260.31345658410754,
            "unit": "iter/sec",
            "range": "stddev: 0.00008660586707107756",
            "extra": "mean: 3.8415224980000175 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 722.2294134604884,
            "unit": "iter/sec",
            "range": "stddev: 0.00034589146765940645",
            "extra": "mean: 1.3846015980000068 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 28.61758761517183,
            "unit": "iter/sec",
            "range": "stddev: 0.00596937743000645",
            "extra": "mean: 34.943546376 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 8505.919286240023,
            "unit": "iter/sec",
            "range": "stddev: 0.0006134610674208687",
            "extra": "mean: 117.56518800004301 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 14759.250064767562,
            "unit": "iter/sec",
            "range": "stddev: 0.0002472884636943026",
            "extra": "mean: 67.75412000011727 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 761.8857266615585,
            "unit": "iter/sec",
            "range": "stddev: 0.00036785987551977116",
            "extra": "mean: 1.312532791999942 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 29.9058858107075,
            "unit": "iter/sec",
            "range": "stddev: 0.007134351617498614",
            "extra": "mean: 33.43823374200005 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 9216.265041501481,
            "unit": "iter/sec",
            "range": "stddev: 0.00006415591368903354",
            "extra": "mean: 108.5038239999534 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 9099.500674011484,
            "unit": "iter/sec",
            "range": "stddev: 0.0000221124930153669",
            "extra": "mean: 109.89613999986148 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 13531.624312620008,
            "unit": "iter/sec",
            "range": "stddev: 0.000021753969389893017",
            "extra": "mean: 73.90095800009533 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 16730.805884187783,
            "unit": "iter/sec",
            "range": "stddev: 0.000019869811236882146",
            "extra": "mean: 59.76998399970057 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2863.0273927645,
            "unit": "iter/sec",
            "range": "stddev: 0.00008894470674186983",
            "extra": "mean: 349.28062600002363 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "622a83131e751d4a8e70d9f47d1b111cc58ebb7f",
          "message": "Merge pull request #767 from simphony/feature/isort_black_pre-commit\n\nCode formatting with black and isort",
          "timestamp": "2022-04-06T17:43:10+02:00",
          "tree_id": "cbb069e70cd148772fb6264d115ff73256accc0b",
          "url": "https://github.com/simphony/osp-core/commit/622a83131e751d4a8e70d9f47d1b111cc58ebb7f"
        },
        "date": 1649259847264,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 673.5271631625781,
            "unit": "iter/sec",
            "range": "stddev: 0.004479077622806471",
            "extra": "mean: 1.484721113999996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 2046.8091162847588,
            "unit": "iter/sec",
            "range": "stddev: 0.000058813707545091677",
            "extra": "mean: 488.56534400000044 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2398.9022009409105,
            "unit": "iter/sec",
            "range": "stddev: 0.00007428058522860329",
            "extra": "mean: 416.8573440000074 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 304.3319112481348,
            "unit": "iter/sec",
            "range": "stddev: 0.00048019311128269564",
            "extra": "mean: 3.2858861100000034 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 502.9053015286179,
            "unit": "iter/sec",
            "range": "stddev: 0.00010402589443904549",
            "extra": "mean: 1.988445929999994 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 994.8023586262152,
            "unit": "iter/sec",
            "range": "stddev: 0.00010835970317999063",
            "extra": "mean: 1.0052247980000395 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 43.54902767599898,
            "unit": "iter/sec",
            "range": "stddev: 0.001001382892580032",
            "extra": "mean: 22.962625192000015 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17372.53777716798,
            "unit": "iter/sec",
            "range": "stddev: 0.00029251219822784574",
            "extra": "mean: 57.56211400007771 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 18238.353097128853,
            "unit": "iter/sec",
            "range": "stddev: 0.00022110377141010436",
            "extra": "mean: 54.82951200004038 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 977.4235127542241,
            "unit": "iter/sec",
            "range": "stddev: 0.00021691087747603005",
            "extra": "mean: 1.0230979579999655 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 43.57788309719501,
            "unit": "iter/sec",
            "range": "stddev: 0.0008782372341168346",
            "extra": "mean: 22.947420317999963 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 12189.92042299152,
            "unit": "iter/sec",
            "range": "stddev: 0.00005058614332253555",
            "extra": "mean: 82.03498999992576 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 16070.875388957074,
            "unit": "iter/sec",
            "range": "stddev: 0.000012570772015358967",
            "extra": "mean: 62.22436399993114 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 23363.099479643137,
            "unit": "iter/sec",
            "range": "stddev: 0.00001142307793281542",
            "extra": "mean: 42.80253999993988 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 21084.384217653445,
            "unit": "iter/sec",
            "range": "stddev: 0.000011305129434435064",
            "extra": "mean: 47.42846600009898 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3877.671981613947,
            "unit": "iter/sec",
            "range": "stddev: 0.00004544895530811452",
            "extra": "mean: 257.8866920001275 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "daed3e44d3ab1430376c73a2747fa33db3d51920",
          "message": "Bump package version to 3.8.0 (#768)",
          "timestamp": "2022-04-07T09:58:30+02:00",
          "tree_id": "de077706c56a971ad15cd1083df21f0d7a7131a3",
          "url": "https://github.com/simphony/osp-core/commit/daed3e44d3ab1430376c73a2747fa33db3d51920"
        },
        "date": 1649318364797,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 706.729652618306,
            "unit": "iter/sec",
            "range": "stddev: 0.004274267070174751",
            "extra": "mean: 1.414968221999997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1991.9301332896055,
            "unit": "iter/sec",
            "range": "stddev: 0.00007485791783144619",
            "extra": "mean: 502.0256400000003 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2228.8671388703347,
            "unit": "iter/sec",
            "range": "stddev: 0.00008724842639765921",
            "extra": "mean: 448.6584159999927 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 269.77759702702673,
            "unit": "iter/sec",
            "range": "stddev: 0.000420667626532043",
            "extra": "mean: 3.7067570140000115 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 457.21264399071765,
            "unit": "iter/sec",
            "range": "stddev: 0.00021635889886891893",
            "extra": "mean: 2.1871661100000157 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 926.268578402757,
            "unit": "iter/sec",
            "range": "stddev: 0.00015666942748455005",
            "extra": "mean: 1.0796004780000032 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 40.81109772948323,
            "unit": "iter/sec",
            "range": "stddev: 0.003145416517506797",
            "extra": "mean: 24.503138989999975 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17086.124764751203,
            "unit": "iter/sec",
            "range": "stddev: 0.0002994539359441104",
            "extra": "mean: 58.52702199992166 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 16557.666992905128,
            "unit": "iter/sec",
            "range": "stddev: 0.00021772882830234917",
            "extra": "mean: 60.394982000090636 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 921.7626755559166,
            "unit": "iter/sec",
            "range": "stddev: 0.0002014187342037845",
            "extra": "mean: 1.0848779479998996 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 41.86738712305356,
            "unit": "iter/sec",
            "range": "stddev: 0.0015566895002730808",
            "extra": "mean: 23.88493929799997 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 12485.52334783745,
            "unit": "iter/sec",
            "range": "stddev: 0.000045482690763635374",
            "extra": "mean: 80.09275799986426 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 15690.255281386973,
            "unit": "iter/sec",
            "range": "stddev: 0.000013814523650329704",
            "extra": "mean: 63.73382600003197 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 23688.186152026345,
            "unit": "iter/sec",
            "range": "stddev: 0.000012175065295034592",
            "extra": "mean: 42.21513599995319 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 20751.041619190753,
            "unit": "iter/sec",
            "range": "stddev: 0.000013332730731422107",
            "extra": "mean: 48.19035200021915 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3215.9279094950202,
            "unit": "iter/sec",
            "range": "stddev: 0.00004107637033783851",
            "extra": "mean: 310.9522440000916 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "820c90e61c04bef72938cc1e7f4d9850927128ed",
          "message": "Merge branch 'master' into dev",
          "timestamp": "2022-04-07T10:36:04+02:00",
          "tree_id": "de077706c56a971ad15cd1083df21f0d7a7131a3",
          "url": "https://github.com/simphony/osp-core/commit/820c90e61c04bef72938cc1e7f4d9850927128ed"
        },
        "date": 1649320880120,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 721.2882890893336,
            "unit": "iter/sec",
            "range": "stddev: 0.004161866018434019",
            "extra": "mean: 1.386408202000001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1963.2393946317798,
            "unit": "iter/sec",
            "range": "stddev: 0.00008300516903627406",
            "extra": "mean: 509.3622320000142 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2254.163762815354,
            "unit": "iter/sec",
            "range": "stddev: 0.00010285594286739592",
            "extra": "mean: 443.6234919999968 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 272.0940308124159,
            "unit": "iter/sec",
            "range": "stddev: 0.000253985643680044",
            "extra": "mean: 3.675200066000011 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 448.55407052340746,
            "unit": "iter/sec",
            "range": "stddev: 0.0003408913928948714",
            "extra": "mean: 2.2293856320000014 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 968.3566382819034,
            "unit": "iter/sec",
            "range": "stddev: 0.00013161655683854783",
            "extra": "mean: 1.03267738400001 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 42.21988475151588,
            "unit": "iter/sec",
            "range": "stddev: 0.001394106642592009",
            "extra": "mean: 23.68552178400003 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 17425.748536985935,
            "unit": "iter/sec",
            "range": "stddev: 0.0003087988414468662",
            "extra": "mean: 57.386343999944245 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 18265.64420464868,
            "unit": "iter/sec",
            "range": "stddev: 0.0002149717177754035",
            "extra": "mean: 54.74758999989149 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 930.691381198661,
            "unit": "iter/sec",
            "range": "stddev: 0.00020015700664223335",
            "extra": "mean: 1.0744700339999653 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 40.48370418807039,
            "unit": "iter/sec",
            "range": "stddev: 0.0023389064921011597",
            "extra": "mean: 24.701296980000087 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 12498.168081049813,
            "unit": "iter/sec",
            "range": "stddev: 0.000049113255101430894",
            "extra": "mean: 80.01172599976769 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 15790.206516007933,
            "unit": "iter/sec",
            "range": "stddev: 0.000014601365345226878",
            "extra": "mean: 63.33039399999052 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 23483.020367182547,
            "unit": "iter/sec",
            "range": "stddev: 0.000012433152438751607",
            "extra": "mean: 42.583960000200705 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 21955.433455928393,
            "unit": "iter/sec",
            "range": "stddev: 0.000011887821413473562",
            "extra": "mean: 45.546812000196724 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 3511.7312225979317,
            "unit": "iter/sec",
            "range": "stddev: 0.00004990098027776281",
            "extra": "mean: 284.75983400011273 usec\nrounds: 500"
          }
        ]
      },
      {
        "commit": {
          "author": {
            "email": "43052541+kysrpex@users.noreply.github.com",
            "name": "José Manuel Domínguez",
            "username": "kysrpex"
          },
          "committer": {
            "email": "noreply@github.com",
            "name": "GitHub",
            "username": "web-flow"
          },
          "distinct": true,
          "id": "f2d15e4595a5c3131d3077a90fe43bb458f9b6fe",
          "message": "Merge pull request #769 from simphony/dev\n\n Merge release 3.8.0",
          "timestamp": "2022-04-07T10:55:11+02:00",
          "tree_id": "de077706c56a971ad15cd1083df21f0d7a7131a3",
          "url": "https://github.com/simphony/osp-core/commit/f2d15e4595a5c3131d3077a90fe43bb458f9b6fe"
        },
        "date": 1649321765783,
        "tool": "pytest",
        "benches": [
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_create",
            "value": 685.2391257117888,
            "unit": "iter/sec",
            "range": "stddev: 0.004395580630266136",
            "extra": "mean: 1.4593445739999957 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_add_default",
            "value": 1901.388971108094,
            "unit": "iter/sec",
            "range": "stddev: 0.00009461064451699352",
            "extra": "mean: 525.9313140000063 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_add_rel",
            "value": 2299.420683033356,
            "unit": "iter/sec",
            "range": "stddev: 0.00009327872999516883",
            "extra": "mean: 434.89214799999854 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_get_byuiduuid",
            "value": 292.6245726932849,
            "unit": "iter/sec",
            "range": "stddev: 0.000331803816666968",
            "extra": "mean: 3.4173480060000028 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byuiduriref",
            "value": 464.0667224589966,
            "unit": "iter/sec",
            "range": "stddev: 0.00017093876434969807",
            "extra": "mean: 2.154862547999995 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byrel",
            "value": 863.6357004426751,
            "unit": "iter/sec",
            "range": "stddev: 0.00035855898173972476",
            "extra": "mean: 1.157895625999977 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_get_byoclass",
            "value": 41.66030315256759,
            "unit": "iter/sec",
            "range": "stddev: 0.001361417593808274",
            "extra": "mean: 24.003665943999938 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduuid",
            "value": 15457.44276948564,
            "unit": "iter/sec",
            "range": "stddev: 0.0003117353113025118",
            "extra": "mean: 64.69375400011756 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byuiduriref",
            "value": 17588.18557954487,
            "unit": "iter/sec",
            "range": "stddev: 0.0002226650279997911",
            "extra": "mean: 56.85634800004635 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iter_byrel",
            "value": 1012.3776142017323,
            "unit": "iter/sec",
            "range": "stddev: 0.00005915461886086931",
            "extra": "mean: 987.7737179999854 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_iter_byoclass",
            "value": 40.50632978663692,
            "unit": "iter/sec",
            "range": "stddev: 0.003028573110601719",
            "extra": "mean: 24.68749958999991 msec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_is_a",
            "value": 10855.385959436544,
            "unit": "iter/sec",
            "range": "stddev: 0.00005496237941505502",
            "extra": "mean: 92.12017000010064 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_oclass",
            "value": 13701.09746067486,
            "unit": "iter/sec",
            "range": "stddev: 0.00001632606011714489",
            "extra": "mean: 72.98685399985061 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_uid",
            "value": 20711.491941127384,
            "unit": "iter/sec",
            "range": "stddev: 0.000014751752157259363",
            "extra": "mean: 48.28237400002422 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_iri",
            "value": 18481.2773756513,
            "unit": "iter/sec",
            "range": "stddev: 0.00001699642203494164",
            "extra": "mean: 54.108813999917516 usec\nrounds: 500"
          },
          {
            "name": "benchmark_cuds_api.py::benchmark_cuds_attributes",
            "value": 2568.4318997416,
            "unit": "iter/sec",
            "range": "stddev: 0.00010325324000458651",
            "extra": "mean: 389.34261799995795 usec\nrounds: 500"
          }
        ]
      }
    ]
  }
}