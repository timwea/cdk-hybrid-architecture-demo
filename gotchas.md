- subnets create their own route tables and associations that override
  my custom route table and association. i have to call subnet.node.try_remove_child() for each subnet
- you have to set subnet_configuration=[] on the vpc construct to prevent it
  from creating its own subnets.
- naming resources is less straightforward, appends extra stuff to names
- may need to switch between high-level constructs and low-level constructs

- on prem arch
1 vpc
1 tgw
2 private subnets, A and B
each subnet has custom route table association
  - subnet A routes traffic locally and to any ip via tgw
  - subnet B routes traffic locally and to any ip via tgw
the tgw route table routes traffic to....