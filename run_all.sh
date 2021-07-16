python cluster.py ../data/events_anomalydetection.h5 --chunk-size 10000 -j 22
mv scalars_* ../2jet/RnD/
python cluster.py ../data/events_LHCO2020_backgroundMC_Pythia.h5 --chunk-size 10000 -j 20
mv scalars_* ../2jet/BBOXMC/
python cluster.py ../data/events_LHCO2020_BlackBox1.h5 --chunk-size 10000 -j 20
mv scalars_* ../2jet/BBOX1/
python cluster.py ../data/events_LHCO2020_BlackBox2.h5 --chunk-size 10000 -j 20
mv scalars_* ../2jet/BBOX2/
python cluster.py ../data/events_LHCO2020_BlackBox3.h5 --chunk-size 10000 -j 20
mv scalars_* ../2jet/BBOX3/