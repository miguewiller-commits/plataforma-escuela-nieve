import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:intl/intl.dart';
// Importamos el modelo y los estilos de la página de clases
// Esto asume que tienes un archivo classes_page.dart, pero para simplificar
// lo hemos integrado aquí. Usamos la paleta de colores del PerfilPage.

// RECUERDA: Si estás en un emulador Android, usa 'http://10.0.2.2:8000'
const String baseUrl = 'http://127.0.0.1:8000';

/* ===================== PALETA DE COLORES ===================== */
// Se usa la misma paleta del PerfilPage.dart
class SkilandColors {
  static const Color primary = Color(0xFF1D4ED8);       
  static const Color background = Color(0xFFF1F5F9);    
  static const Color surface = Colors.white;
  static const Color textMain = Color(0xFF0F172A);      
  static const Color textSecondary = Color(0xFF334155); 
  static const Color primaryAccent = Color(0xFF2563EB); // Azul Royal vibrante
  static const Color navyDark = Color(0xFF0A2342); 
  static const Color navyMedium = Color(0xFF2D4F7C);
  static const Color textLight = Color(0xFF94A3B8); 
  static const Color ski = Color(0xFF00C897); 
  static const Color snow = Color(0xFF3B82F6);
}

class TextStyles {
  static const TextStyle cardTitle = TextStyle(
    fontSize: 18, fontWeight: FontWeight.w800, color: SkilandColors.navyDark);
  static const TextStyle cardDetail = TextStyle(
    fontSize: 13, fontWeight: FontWeight.w700, color: SkilandColors.navyMedium);
}


/* ===================== MODELO DE CLASE ===================== */
// Idealmente, este modelo Clase debería estar en un archivo aparte (ej: models.dart)
// pero lo incluimos aquí para que el Historial sea auto-contenido.
class Clase {
  final int id;
  final DateTime horaInicio;
  final DateTime horaFin;
  final String disciplina;
  final int nivel;
  final String nombreTitular;
  final String telefono;
  final int cantidadAlumnos;

  Clase({
    this.id = 0,
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
      id: json['id_clase'] ?? 0,
      horaInicio: DateTime.parse(json['hora_inicio'] as String).toLocal(),
      horaFin: DateTime.parse(json['hora_fin'] as String).toLocal(),
      disciplina: json['disciplina_clase']?.toString() ?? '',
      nivel: (json['nivel_clase'] as num?)?.toInt() ?? 0,
      nombreTitular: json['nombre_titular']?.toString() ?? 'Sin nombre',
      telefono: json['titular_telefono']?.toString() ?? '',
      cantidadAlumnos: (json['cantidad_alumnos'] as num?)?.toInt() ?? 0,
    );
  }
}

/* ===================== PANTALLA HISTORIAL (REUTILIZABLE) ===================== */

class HistorialClasesPage extends StatefulWidget {
  final String token;
  final DateTime? fechaInicio;     // Inicio del filtro (usado para Historial Mensual)
  final bool isMonthlyDetail;       // Indica si el título debe ser "Clases de Ene 2025"

  const HistorialClasesPage({
    super.key, 
    required this.token, 
    this.fechaInicio,
    this.isMonthlyDetail = false
  });

  @override
  State<HistorialClasesPage> createState() => _HistorialClasesPageState();
}

class _HistorialClasesPageState extends State<HistorialClasesPage> {
  bool _loading = false;
  String? _error;
  List<Clase> _clases = []; 

  @override
  void initState() {
    super.initState();
    _fetchHistorial();
  }

  // --- LÓGICA DE CONEXIÓN AL BACKEND ---
  Future<void> _fetchHistorial() async {
    setState(() { _loading = true; _error = null; });
    try {
      final urlBuilder = StringBuffer('$baseUrl/api/instructor/clases/?');
      
      // 1. LÓGICA DE FILTRADO
      if (widget.fechaInicio != null) {
          // Filtro para el detalle mensual
          final startOfMonth = DateFormat('yyyy-MM-dd').format(widget.fechaInicio!);
          // El último día del mes
          final endOfMonth = DateTime(widget.fechaInicio!.year, widget.fechaInicio!.month + 1, 1).add(const Duration(microseconds: -1));
          final endOfMonthStr = DateFormat('yyyy-MM-dd').format(endOfMonth);

          // Pasamos los filtros 'desde' y 'hasta' al backend
          urlBuilder.write('desde=$startOfMonth&hasta=$endOfMonthStr'); 
      }
      
      final url = Uri.parse(urlBuilder.toString());

      final resp = await http.get(
        url,
        headers: {'Authorization': 'Bearer ${widget.token}', 'Content-Type': 'application/json'},
      );

      if (resp.statusCode == 200) {
        final rawData = jsonDecode(utf8.decode(resp.bodyBytes));
        final data = rawData is Map && rawData.containsKey('results') ? rawData['results'] : rawData; 
        
        if (data is List) {
          final clases = data.map((e) => Clase.fromJson(e)).toList();
          // Ordenamos de la más reciente a la más antigua
          clases.sort((a, b) => b.horaInicio.compareTo(a.horaInicio)); 
          if (mounted) setState(() => _clases = clases);
        } else {
           throw Exception("Formato de respuesta JSON incorrecto");
        }
      } else {
        if (mounted) setState(() => _error = 'Error ${resp.statusCode}: No se pudo cargar el historial.');
      }
    } catch (e) {
      if (mounted) setState(() => _error = 'Sin conexión o error de red.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  // --- WIDGETS UI ---

  @override
  Widget build(BuildContext context) {
    // Título dinámico
    final title = widget.isMonthlyDetail && widget.fechaInicio != null
        ? "Clases de ${DateFormat('MMM yyyy', 'es').format(widget.fechaInicio!)}"
        : "Historial Completo";

    return Scaffold(
      backgroundColor: SkilandColors.background,
      appBar: AppBar(
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.w800, color: SkilandColors.navyDark),
        ),
        centerTitle: true,
        backgroundColor: SkilandColors.surface,
        elevation: 1,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: SkilandColors.primaryAccent),
            onPressed: _fetchHistorial,
          )
        ],
      ),
      body: _buildContent(),
    );
  }

  Widget _buildContent() {
    if (_loading) return const Center(child: CircularProgressIndicator(color: SkilandColors.primaryAccent));
    
    if (_error != null) {
      return Center(
        child: Text(_error!),
      );
    }
    
    if (_clases.isEmpty) {
      final emptyMessage = widget.isMonthlyDetail
          ? "No hay clases registradas este mes."
          : "Aún no hay clases registradas en tu historial.";

      return Center(
        child: Text(emptyMessage, style: TextStyles.cardDetail),
      );
    }

    // Listado de Clases Históricas
    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      itemCount: _clases.length,
      itemBuilder: (context, index) {
        final clase = _clases[index];
        return _buildHistorialCard(clase);
      },
    );
  }

  // Helper para construir la tarjeta de historial (más simple)
  Widget _buildHistorialCard(Clase clase) {
    final dateFormat = DateFormat('EEE, d MMM yyyy');
    final timeFormat = DateFormat('HH:mm');
    final isSki = clase.disciplina.toLowerCase() == 'ski';
    final accentColor = isSki ? SkilandColors.ski : SkilandColors.snow;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Icon(
          isSki ? Icons.downhill_skiing_rounded : Icons.snowboarding_rounded,
          color: accentColor,
        ),
        title: Text(
          "${clase.nombreTitular} (${clase.cantidadAlumnos} Pax)",
          style: TextStyles.cardTitle.copyWith(fontSize: 16)
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              "${dateFormat.format(clase.horaInicio)}",
              style: TextStyles.cardDetail.copyWith(color: SkilandColors.textLight)
            ),
            Text(
              "De ${timeFormat.format(clase.horaInicio)} a ${timeFormat.format(clase.horaFin)}",
              style: TextStyles.cardDetail.copyWith(fontSize: 12)
            ),
          ],
        ),
        trailing: Text(
          "Nivel ${clase.nivel}",
          style: TextStyle(fontWeight: FontWeight.bold, color: SkilandColors.navyMedium)
        ),
        onTap: () {
          // Aquí puedes implementar una vista detallada si es necesario
        },
      ),
    );
  }
}