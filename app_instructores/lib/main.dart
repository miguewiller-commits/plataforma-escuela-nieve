import 'package:flutter/material.dart';
import 'pages/login_page.dart';

import 'package:intl/intl.dart';
import 'package:intl/date_symbol_data_local.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar datos locales para español
  await initializeDateFormatting('es', null);
  Intl.defaultLocale = 'es';

  runApp(const MyApp());
}


class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'App Instructores',
      debugShowCheckedModeBanner: false,
      home: const LoginPage(),
    );
  }
}
