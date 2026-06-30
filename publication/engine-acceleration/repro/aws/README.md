# Optional: how the paper's timings were provisioned

These scripts spin up a dedicated AWS instance, ship the benchmark bundle, and run the harness
under `nohup`. They are a **convenience, not part of the reproduction path** — the benchmark runs
on any machine via `../bench_scaling.sh`. We used dedicated instances only to obtain quiet,
uncontended hardware (shared/contended hosts produce unreliable timings).

- `crosshw_launch.sh <instance-type> <name>` — launch one box, ship the bundle, run the sweep.
- `aws_ladder_launch.sh` — single-box variant for the full ladder study.

They assume an AWS profile, an AMI with the NetCDF runtime, a security group allowing SSH, and a
key pair — all installation-specific and intentionally not hard-coded here.
