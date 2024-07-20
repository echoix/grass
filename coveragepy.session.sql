SELECT *
, replace(path,"/usr/local/grass85/scripts/","")
, replace(path,"/usr/local/grass85/scripts/","/usr/local/grass85/scripts-fixed/")
, replace(path,"/usr/local/grass85/scripts/", "/usr/local/grass85/scripts-fixed/") || "/" || replace(path,"/usr/local/grass85/scripts/","") || ".py"

from file 
where (path not like "/workspace/grass/%" ) and (path like "/usr/local/grass%/scripts/%");

-- select * from tracer where tracer.tracer <> "";

select * from line_bits 
Inner join file ON file.id = line_bits.file_id
where (file.path not like "/workspace/grass/%" ) and (file.path like "/usr/local/grass%/scripts/%");


-- insert into file (path)
-- SELECT 
--  replace(path,"/usr/local/grass85/scripts/", "/usr/local/grass85/scripts-fixed/") || "/" || replace(path,"/usr/local/grass85/scripts/","") || ".py"
-- from file 
-- where (path not like "/workspace/grass/%" ) and (path like "/usr/local/grass%/scripts/%");

SELECT *
, replace(path,"/usr/local/grass85/scripts/","")
, replace(path,"/usr/local/grass85/scripts/","/usr/local/grass85/scripts-fixed/")
, replace(path,"/usr/local/grass85/scripts/", "/usr/local/grass85/scripts-fixed/") || "/" || replace(path,"/usr/local/grass85/scripts/","") || ".py"

from file 
where ((path not like "/workspace/grass/%" ) and (path like "/usr/local/grass%/scripts/%")) or (path like "/usr/local/grass%/scripts-fixed/%");

select f1.*, f2.id as f2id, f2.path as f2path 
from file as f1
inner join file as f2
on f1.path = replace(f2.path,"/usr/local/grass85/scripts/", "/usr/local/grass85/scripts-fixed/") || "/" || replace(f2.path,"/usr/local/grass85/scripts/","") || ".py";


