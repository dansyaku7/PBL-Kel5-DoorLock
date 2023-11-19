<?php

$hostname = "localhost";
$username = "root";
$password = "";
$databasename = "doorlock";

// Menggunakan mysqli untuk koneksi database
$connection = mysqli_connect($hostname, $username, $password, $databasename) or die(mysqli_error($connection));
?>