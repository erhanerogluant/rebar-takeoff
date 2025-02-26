from rebar_calculator import RebarCalculator

def main():
    calculator = RebarCalculator()
    
    # Örnek kullanım
    calculator.process_text("ƒ10 Etr. l= 168")
    calculator.process_text("Etr.%%C10/8")
    calculator.process_dimension(291.0)
    
    calculator.process_text("2x%%C12/15 L=185")
    calculator.process_dimension(171.0)
    
    calculator.export_results("demir_metraji")

if __name__ == "__main__":
    main() 