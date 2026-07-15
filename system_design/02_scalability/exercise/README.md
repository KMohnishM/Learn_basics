# Exercise: Weighted Round Robin Load Balancing

In the lab, Nginx routes traffic equally across all three backend servers (Round Robin).

However, in the real world, you rarely have servers of identical power. Imagine `web1` runs on a massive 16-core machine, while `web2` and `web3` run on tiny 2-core machines.

If you route equally, `web2` and `web3` will crash under load while `web1` sits mostly idle.

## Your Task

Modify the `labs/nginx.conf` file to implement **Weighted Round Robin**.

Configure the upstream block so that:
- `web1` receives **60%** of all traffic.
- `web2` receives **20%** of all traffic.
- `web3` receives **20%** of all traffic.

**How to verify your answer:**
1. Update `labs/nginx.conf`.
2. Run `docker-compose up --build -d` in the `labs/` directory to restart Nginx.
3. Run `python load_test.py`.
4. You should see `web1` handling roughly 60 requests out of 100, with the others handling 20 each.

*Hint: Check the Nginx documentation for the `weight` parameter in the `upstream` block.*

Check the `solution/` folder when you are finished!
