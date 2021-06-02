sizes=(1 10 100 1000 10000 100000)
args=()

for size in ${sizes[@]}; do
    chunk=$(python -c "from math import ceil; print(ceil($size/10))")
    script="python cluster.py ../../data/events_anomalydetection.h5 -j 5 --chunk-size ${chunk} --max-events ${size}"
    
    args+=("${script}")
done

hyperfine --warmup 1 "${args[@]}" > log_benchmark_mpi.txt
