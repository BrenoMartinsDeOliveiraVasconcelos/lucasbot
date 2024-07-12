-- --------------------------------------------------------
-- Servidor:                     192.168.1.21
-- Versão do servidor:           10.11.6-MariaDB-0+deb12u1 - Debian 12
-- OS do Servidor:               debian-linux-gnu
-- HeidiSQL Versão:              12.7.0.6850
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Copiando estrutura do banco de dados para lucasbot
CREATE DATABASE IF NOT EXISTS `lucasbot` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `lucasbot`;

-- Copiando estrutura para tabela lucasbot.splashes
CREATE TABLE IF NOT EXISTS `splashes` (
  `id` int(10) unsigned NOT NULL,
  `owner` int(10) unsigned NOT NULL,
  `text` varchar(128) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `owner` (`owner`),
  CONSTRAINT `owner` FOREIGN KEY (`owner`) REFERENCES `users` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados foi desmarcado.

-- Copiando estrutura para tabela lucasbot.statistics
CREATE TABLE IF NOT EXISTS `statistics` (
  `id` int(10) unsigned NOT NULL,
  `owner` int(10) unsigned NOT NULL,
  `datetime` datetime NOT NULL,
  `members` int(255) unsigned NOT NULL,
  `growt` int(255) NOT NULL,
  `growt_percent` decimal(65,9) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `stat_owner` (`owner`),
  CONSTRAINT `stat_owner` FOREIGN KEY (`owner`) REFERENCES `users` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados foi desmarcado.

-- Copiando estrutura para tabela lucasbot.subreddits
CREATE TABLE IF NOT EXISTS `subreddits` (
  `subreddit` varchar(21) NOT NULL DEFAULT '0',
  `user` int(10) unsigned NOT NULL DEFAULT 0,
  PRIMARY KEY (`subreddit`) USING BTREE,
  UNIQUE KEY `subreddit` (`subreddit`),
  KEY `user_sub` (`user`),
  CONSTRAINT `user_sub` FOREIGN KEY (`user`) REFERENCES `users` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Lista de subs do bot';

-- Exportação de dados foi desmarcado.

-- Copiando estrutura para tabela lucasbot.users
CREATE TABLE IF NOT EXISTS `users` (
  `id` int(10) unsigned NOT NULL,
  `username` varchar(20) NOT NULL DEFAULT '',
  `client` varchar(50) NOT NULL,
  `secret` varchar(50) NOT NULL,
  `password` varchar(1000) NOT NULL,
  `user_agent` varchar(1000) NOT NULL,
  `subreddit` varchar(21) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `client` (`client`),
  UNIQUE KEY `secret` (`secret`),
  UNIQUE KEY `id` (`id`),
  KEY `subredditfk` (`subreddit`),
  CONSTRAINT `subredditfk` FOREIGN KEY (`subreddit`) REFERENCES `subreddits` (`subreddit`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Exportação de dados foi desmarcado.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
