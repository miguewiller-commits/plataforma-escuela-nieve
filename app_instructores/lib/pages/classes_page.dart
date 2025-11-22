import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';

import 'login_page.dart';

const String baseUrl = 'http://localhost:8000';

/* ===================== MODELO ===================== */

class Clase {
  final DateTime horaInicio;
  final DateTime horaFin;
  final String disciplina;
  final int nivel;
  final String nombreTitular;
  final String telefono;
  final int cantidadAlumnos;

  Clase({
    required this.horaInicio,
    required this.horaFin,
    required this.disciplina,
    required this.nivel,
    required this.nombreTitular,
    required this.telefono,
    required this.cantidadAlumnos,
  });

  factory Clase.fromJson(Map<String, dynamic> json) {
    return Clase(
      // toLocal para corregir el desfase horario
      horaInicio: DateTime.parse(json['hora_inicio'] as String).toLocal(),
      horaFin: DateTime.parse(json['hora_fin'] as String).toLocal(),
      disciplina: json['disciplina_clase']?.toString() ?? '',
      nivel: (json['nivel_clase'] as num?)?.toInt() ?? 0,
      nombreTitular: json['nombre_titular']?.toString() ?? '',
      telefono: json['titular_telefono']?.toString() ?? '',
      cantidadAlumnos: (json['cantidad_alumnos'] as num?)?.toInt() ?? 0,
    );
  }
}

/* ===================== PANTALLA CLASES ===================== */

class ClassesPage extends StatefulWidget {
  final String token;

  const ClassesPage({super.key, required this.token});

  @override
  State<ClassesPage> createState() => _ClassesPageState();
}

class _ClassesPageState extends State<ClassesPage> {
  bool _loading = false;
  String? _error;
  List<Clase> _clases = [];
  DateTime _selectedDate = DateTime.now();

  @override
  void initState() {
    super.initState();
    _fetchClases();
  }

  Future<void> _fetchClases() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final fecha = _selectedDate.toIso8601String().substring(0, 10);
      final url =
          Uri.parse('$baseUrl/api/instructor/clases/?fecha=$fecha');

      final resp = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
        },
      );

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as List<dynamic>;
        final clases = data
            .map((e) => Clase.fromJson(e as Map<String, dynamic>))
            .toList();

        if (mounted) {
          setState(() {
            _clases = clases;
          });
        }
      } else {
        if (mounted) {
          setState(() {
            _error = 'Error ${resp.statusCode}: ${resp.body}';
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error al cargar clases: $e';
        });
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _cambiarDia(int delta) {
    setState(() {
      _selectedDate = _selectedDate.add(Duration(days: delta));
    });
    _fetchClases();
  }

  @override
  Widget build(BuildContext context) {
    final fechaLarga = DateFormat('EEEE d \'de\' MMMM', 'es')
        .format(_selectedDate);
    final fechaCorta =
        '${_selectedDate.day.toString().padLeft(2, '0')}/${_selectedDate.month.toString().padLeft(2, '0')}/${_selectedDate.year}';

    return Scaffold(
      backgroundColor: const Color(0xfff3f4f6),
      appBar: AppBar(
        title: const Text('Mis clases del día'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: const Color(0xff0e62f0),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (_) => const LoginPage()),
          ),
        ),
      ),
      body: Column(
        children: [
          // ===== Cabecera con fecha y resumen =====
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
            decoration: const BoxDecoration(
              color: Color(0xff0e62f0),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(20),
                bottomRight: Radius.circular(20),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Selector de fecha con flechas
                Row(
                  children: [
                    IconButton(
                      icon: const Icon(Icons.chevron_left, color: Colors.white),
                      onPressed: () => _cambiarDia(-1),
                    ),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            fechaLarga,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            fechaCorta,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Color(0xffdbeafe),
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon:
                          const Icon(Icons.chevron_right, color: Colors.white),
                      onPressed: () => _cambiarDia(1),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                // Resumen de clases del día
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.event_available,
                              size: 16, color: Colors.white),
                          const SizedBox(width: 6),
                          Text(
                            _clases.isEmpty
                                ? 'Sin clases para este día'
                                : '${_clases.length} clase(s) asignada(s)',
                            style: const TextStyle(
                              fontSize: 12,
                              color: Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.refresh, color: Colors.white),
                      onPressed: _fetchClases,
                      tooltip: 'Actualizar',
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 8),

          // ===== Contenido principal =====
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Padding(
                          padding:
                              const EdgeInsets.symmetric(horizontal: 24.0),
                          child: Text(
                            _error!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(color: Colors.redAccent),
                          ),
                        ),
                      )
                    : _clases.isEmpty
                        ? Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: const [
                              Icon(Icons.hourglass_empty,
                                  size: 60, color: Colors.grey),
                              SizedBox(height: 12),
                              Text(
                                'No tienes clases en esta fecha',
                                style: TextStyle(
                                    color: Colors.grey, fontSize: 14),
                              ),
                            ],
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
                            itemCount: _clases.length,
                            itemBuilder: (context, index) {
                              final c = _clases[index];
                              return _buildClassCard(c);
                            },
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildClassCard(Clase c) {
    final horaStr =
        '${c.horaInicio.hour.toString().padLeft(2, '0')}:${c.horaInicio.minute.toString().padLeft(2, '0')}'
        ' – '
        '${c.horaFin.hour.toString().padLeft(2, '0')}:${c.horaFin.minute.toString().padLeft(2, '0')}';

    String discLabel = c.disciplina.toUpperCase();
    Color chipBg;
    Color chipText;

    if (c.disciplina == 'ski') {
      chipBg = const Color(0xffecfdf5);
      chipText = const Color(0xff047857);
      discLabel = 'Ski';
    } else if (c.disciplina == 'snow') {
      chipBg = const Color(0xffeff6ff);
      chipText = const Color(0xff1d4ed8);
      discLabel = 'Snow';
    } else {
      chipBg = const Color(0xfff3f4f6);
      chipText = const Color(0xff374151);
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Columna hora
          SizedBox(
            width: 80,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Hora',
                  style: TextStyle(fontSize: 11, color: Colors.grey),
                ),
                const SizedBox(height: 2),
                Text(
                  horaStr,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Info principal
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: chipBg,
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(
                          color: chipText.withOpacity(0.3),
                        ),
                      ),
                      child: Text(
                        discLabel,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: chipText,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'Nivel ${c.nivel}',
                      style: const TextStyle(
                        fontSize: 11,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  c.nombreTitular,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    const Icon(Icons.person_outline,
                        size: 14, color: Colors.grey),
                    const SizedBox(width: 4),
                    Text(
                      '${c.cantidadAlumnos} alumno(s)',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    const Icon(Icons.phone_outlined,
                        size: 14, color: Colors.grey),
                    const SizedBox(width: 4),
                    Text(
                      c.telefono,
                      style: const TextStyle(
                        fontSize: 12,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
