window.BENCHMARK_DATA = {
  "lastUpdate": 1624545954356,
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
      }
    ]
  }
}