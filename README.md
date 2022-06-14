# Curve Alert Bot
 Get Curve Pool reserves and set alerts


 ## Commands

 ```
 /reserves - get pool reserves of all supported pools
 /reserves (3pool/frax/usdd/steth) - get pool reserves of specific pool

 /addalert (3pool/frax/usdd/steth, percentage_1, percentage_2, percentage_3) - Add alert for the corresponding pool, Only 1 percentage can be >0. The rest must be 0

 /getalert (3pool/frax/usdd/steth) - get list of current alert for the pool

 /removealert (3pool/frax/usdd/steth) - remove all alert for the pool
 ```
