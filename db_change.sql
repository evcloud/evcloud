ALTER TABLE `image_image` ADD COLUMN `snap_exists` TINYINT NOT NULL DEFAULT '0' AFTER `type_id`;
ALTER TABLE `network_vlan` ADD COLUMN `subnetip` CHAR(39) NULL DEFAULT NULL AFTER `remarks`;
ALTER TABLE `network_vlan` ADD COLUMN `netmask` CHAR(39) NULL DEFAULT NULL AFTER `subnetip`;
ALTER TABLE `network_vlan` ADD COLUMN `gateway` CHAR(39) NULL DEFAULT NULL AFTER `netmask`;
ALTER TABLE `network_vlan` ADD COLUMN `dnsserver` CHAR(39) NULL DEFAULT NULL AFTER `gateway`;



#--------------------------------------


ALTER TABLE `image_imagetype`
    CHANGE COLUMN `code` `code` INT(11) NOT NULL AUTO_INCREMENT FIRST;
ALTER TABLE `image_imagetype`
    ADD COLUMN `order` INT(11) NOT NULL DEFAULT '0' ;
ALTER TABLE `compute_center`
    ADD COLUMN `order` INT(11) NOT NULL DEFAULT '0' AFTER `desc`;
ALTER TABLE `image_image`
    ADD COLUMN `order` INT(11) NOT NULL DEFAULT '0' AFTER `snap_exists`;
ALTER TABLE `compute_group`
    ADD COLUMN `order` INT(11) NOT NULL DEFAULT '0' AFTER `desc`;
ALTER TABLE `network_vlantype`
    ADD COLUMN `order` INT(11) NOT NULL DEFAULT '0' AFTER `name`;
ALTER TABLE `network_vlan`
    ADD COLUMN `order` INT(11) NOT NULL DEFAULT '0' AFTER `dnsserver`;
ALTER TABLE `network_vlan`
    CHANGE COLUMN `type_id` `type_id` INT(11) NOT NULL AFTER `br`,
    DROP FOREIGN KEY `network_vlan_type_id_13b82de62e3b45f0_fk_network_vlantype_code`;
ALTER TABLE `network_vlantype`
    CHANGE COLUMN `code` `code` INT(11) NOT NULL AUTO_INCREMENT FIRST;
ALTER TABLE `image_image`
    CHANGE COLUMN `type_id` `type_id` INT(11) NOT NULL AFTER `xml_id`;


#-------------------------------------------------

ALTER TABLE `storage_cephhost`
    ADD COLUMN `username` VARCHAR(100) NOT NULL AFTER `uuid`;

#---------------------------------

ALTER TABLE `storage_cephpool`
    ADD COLUMN `enable` tinyint(1) NOT NULL DEFAULT 1;


ALTER TABLE `storage_cephpool`
    ADD COLUMN `remarks` longtext;



#-------------------------------
ALTER TABLE `compute_vm`
    ADD COLUMN `ceph_id` INT(11) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `ceph_host` VARCHAR(100) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `ceph_pool` VARCHAR(100) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `ceph_uuid` VARCHAR(100) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `ceph_port` INT(11) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `ceph_username` VARCHAR(100) NOT NULL;


ALTER TABLE `compute_vm`
    ADD COLUMN `vlan_id` INT(11) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `ipv4` VARCHAR(100) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `vlan_name` VARCHAR(100) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `mac` VARCHAR(100) NOT NULL;

ALTER TABLE `compute_vm`
    ADD COLUMN `br` VARCHAR(100) NOT NULL;

update compute_vm a, image_image b, storage_cephpool c, storage_cephhost d set a.ceph_id = b.cephpool_id, a.ceph_host = d.host, a.ceph_pool=c.pool, a.ceph_uuid=d.uuid, a.ceph_port=d.port, a.ceph_username=d.username where a.image_id=b.id and b.cephpool_id=c.id and c.host_id=d.id;
update compute_vm a, network_macip b, network_vlan c set a.vlan_id = c.id, a.ipv4=b.ipv4, a.vlan_name=c.vlan, a.mac=b.mac, a.br=c.br where a.uuid = b.vmid and b.vlan_id = c.id;
