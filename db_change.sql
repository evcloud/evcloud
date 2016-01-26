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
