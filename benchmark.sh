sizes=(1 10 100 1000 10000 100000)
args=()

for size in ${sizes[@]}; do
    script="python cluster.py ../../data/events_anomalydetection.h5 -j 1 --chunk-size ${size} --max-events ${size}"
    
    args+=("${script}")
done

hyperfine --warmup 1 "${args[@]}" > log_benchmark.txt