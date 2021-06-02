window.BENCHMARK_DATA = {
  "lastUpdate": 1622624763054,
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
      }
    ]
  }
}