# Exercise: Slowly Changing Dimensions (SCD Type 2)

In the lab's `dim_customer` table, we used an SCD Type 1 approach (if a user moves, we just `UPDATE` their row). This destroys historical accuracy.

## Your Task

Redesign the `dim_customer` table in `solution/scd_type_2.sql` to implement **SCD Type 2**.

1. You must keep the surrogate key (`customer_sk`) and the natural key (`customer_id`).
2. Add the three standard columns required for SCD Type 2 tracking:
   - A column to indicate when this record became valid.
   - A column to indicate when this record expired.
   - A boolean column to quickly query if this is the currently active record for the user.

3. Write an `INSERT` statement showing how you would add a brand new customer (Alice, living in New York).
4. Write the SQL commands (an `UPDATE` followed by an `INSERT`) showing how you would handle Alice moving to California on '2023-05-01'.
